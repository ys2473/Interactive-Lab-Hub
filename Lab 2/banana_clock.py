import math
import subprocess
import time
from datetime import datetime
from pathlib import Path

import adafruit_rgb_display.st7789 as st7789
import board
import digitalio

from adafruit_seesaw import rotaryio, seesaw
from PIL import (
    Image,
    ImageChops,
    ImageDraw,
    ImageFont,
    ImageOps,
    ImageSequence,
)


# Display setup
cs_pin = digitalio.DigitalInOut(board.D5)
dc_pin = digitalio.DigitalInOut(board.D25)

spi = board.SPI()

display = st7789.ST7789(
    spi,
    cs=cs_pin,
    dc=dc_pin,
    rst=None,
    baudrate=64000000,
    width=135,
    height=240,
    x_offset=53,
    y_offset=40,
)

width = display.height
height = display.width
rotation = 90

image = Image.new("RGB", (width, height))
draw = ImageDraw.Draw(image)


# Fonts
font_time = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    22,
)

font_date = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    18,
)

font_small = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    16,
)

font_timer = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    48,
)

center_time_font = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    38,
)

center_date_font = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    18,
)


# Backlight setup
backlight = digitalio.DigitalInOut(board.D22)
backlight.switch_to_output(value=True)


# Button setup
button_a = digitalio.DigitalInOut(board.D23)
button_b = digitalio.DigitalInOut(board.D24)

button_a.switch_to_input(pull=digitalio.Pull.UP)
button_b.switch_to_input(pull=digitalio.Pull.UP)


# I2C STEMMA QT rotary encoder setup
i2c = board.I2C()
seesaw_device = seesaw.Seesaw(i2c, addr=0x36)
encoder = rotaryio.IncrementalEncoder(seesaw_device)

last_encoder_position = encoder.position


# Program state
mode = "clock"

last_a_pressed = False
last_b_pressed = False

a_press_started = None
a_long_press_handled = False

LONG_PRESS_SECONDS = 1.5


# Timer settings
DEFAULT_TIMER_SECONDS = 0
MIN_TIMER_SECONDS = 0
MAX_TIMER_SECONDS = 60 * 60
ALARM_RESPONSE_SECONDS = 10.0

selected_seconds = DEFAULT_TIMER_SECONDS

# Timer state can be:
# "select", "running", "alarming", or "result".
timer_state = "select"

timer_start_time = 0.0
timer_end_time = 0.0
timer_total_seconds = 0

alarm_started_at = 0.0
alarm_process = None

timer_result_image = None


# File locations
BASE_DIR = Path(__file__).resolve().parent

ANIMATION_PATH = (
    BASE_DIR / "banana-animation-2s-once.gif"
)

GOOD_RESULT_ANIMATION_PATH = (
    BASE_DIR / "banana-peel-trash-2s-message-once.gif"
)

BAD_RESULT_ANIMATION_PATH = (
    BASE_DIR
    / "rotten-banana-2s-centered-clean-v2-once.gif"
)


# Load and resize all twelve banana images.
banana_images = []

for image_number in range(1, 13):
    image_path = (
        BASE_DIR / f"banana_{image_number:02d}.png"
    )

    banana = Image.open(image_path).convert("RGB")

    black_background = Image.new(
        "RGB",
        banana.size,
        (0, 0, 0),
    )

    bounding_box = ImageChops.difference(
        banana,
        black_background,
    ).getbbox()

    if bounding_box:
        banana = banana.crop(bounding_box)

    banana.thumbnail(
        (159, 73),
        Image.Resampling.LANCZOS,
    )

    banana_images.append(banana)


def format_timer(total_seconds):
    """Convert seconds into MM:SS format."""
    total_seconds = int(total_seconds)

    minutes = total_seconds // 60
    seconds = total_seconds % 60

    return f"{minutes:02d}:{seconds:02d}"


def stop_alarm():
    """Stop the alarm sound if it is running."""
    global alarm_process

    if alarm_process is not None:
        if alarm_process.poll() is None:
            alarm_process.terminate()

            try:
                alarm_process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                alarm_process.kill()
                alarm_process.wait()

        alarm_process = None


def start_alarm():
    """Start a continuous alarm through the USB speaker."""
    global alarm_process

    stop_alarm()

    alarm_process = subprocess.Popen(
        [
            "speaker-test",
            "-t",
            "sine",
            "-f",
            "880",
            "-c",
            "1",
            "-l",
            "0",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def play_banana_animation():
    """Play the clock banana animation once."""
    with Image.open(ANIMATION_PATH) as animation:
        for gif_frame in ImageSequence.Iterator(animation):
            duration_ms = gif_frame.info.get(
                "duration",
                170,
            )

            frame = gif_frame.convert("RGB")
            frame = ImageOps.contain(
                frame,
                (width, height),
            )

            screen_image = Image.new(
                "RGB",
                (width, height),
                "black",
            )

            frame_x = (width - frame.width) // 2
            frame_y = (height - frame.height) // 2

            screen_image.paste(
                frame,
                (frame_x, frame_y),
            )

            display.image(screen_image, rotation)
            time.sleep(duration_ms / 1000.0)


def play_result_animation(animation_path):
    """Play one result animation and return its final frame."""
    final_screen_image = None

    with Image.open(animation_path) as animation:
        for gif_frame in ImageSequence.Iterator(animation):
            duration_ms = gif_frame.info.get(
                "duration",
                170,
            )

            frame = gif_frame.convert("RGB")
            frame = ImageOps.contain(
                frame,
                (width, height),
            )

            screen_image = Image.new(
                "RGB",
                (width, height),
                "black",
            )

            frame_x = (width - frame.width) // 2
            frame_y = (height - frame.height) // 2

            screen_image.paste(
                frame,
                (frame_x, frame_y),
            )

            display.image(screen_image, rotation)
            final_screen_image = screen_image.copy()

            time.sleep(duration_ms / 1000.0)

    return final_screen_image


def show_centered_datetime():
    """Display the current time and date in the center."""
    now = datetime.now()

    time_text = now.strftime("%I:%M %p").lstrip("0")
    date_text = now.strftime("%B %d, %Y")

    screen_image = Image.new(
        "RGB",
        (width, height),
        "black",
    )

    screen_draw = ImageDraw.Draw(screen_image)

    screen_draw.text(
        (width // 2, height // 2 - 18),
        time_text,
        font=center_time_font,
        fill="white",
        anchor="mm",
    )

    screen_draw.text(
        (width // 2, height // 2 + 28),
        date_text,
        font=center_date_font,
        fill="white",
        anchor="mm",
    )

    display.image(screen_image, rotation)


def announce_current_time():
    """Speak only the hour, minute, and AM or PM."""
    now = datetime.now()
    spoken_time = now.strftime("%I:%M %p").lstrip("0")

    print(f"Speaking: {spoken_time}")

    subprocess.run(
        [
            "espeak-ng",
            "-v",
            "en-us",
            "-s",
            "135",
            spoken_time,
        ],
        check=False,
    )


while True:
    # Buttons are active-low.
    a_pressed = not button_a.value
    b_pressed = not button_b.value

    # Record when Button A is first pressed.
    if a_pressed and not last_a_pressed:
        a_press_started = time.monotonic()
        a_long_press_handled = False

    # Play the clock animation after Button A is held.
    if (
        a_pressed
        and a_press_started is not None
        and not a_long_press_handled
        and time.monotonic() - a_press_started
        >= LONG_PRESS_SECONDS
    ):
        stop_alarm()

        print("Playing banana animation")
        play_banana_animation()

        show_centered_datetime()
        announce_current_time()

        mode = "clock"
        print("Clock mode")

        a_long_press_handled = True

    # A short press selects clock mode.
    if not a_pressed and last_a_pressed:
        if not a_long_press_handled:
            stop_alarm()

            mode = "clock"
            print("Clock mode")

        a_press_started = None
        a_long_press_handled = False

    # Button B controls timer mode.
    if b_pressed and not last_b_pressed:
        if mode != "timer":
            # Enter timer selection mode.
            stop_alarm()

            mode = "timer"
            timer_state = "select"
            selected_seconds = DEFAULT_TIMER_SECONDS
            timer_result_image = None

            last_encoder_position = encoder.position

            print("Timer selection mode")

        elif timer_state == "select":
            if selected_seconds <= 0:
                # Do not start a zero-second timer.
                print("Select at least one second")

            else:
                # Start the countdown.
                timer_total_seconds = selected_seconds
                timer_start_time = time.monotonic()
                timer_end_time = (
                    timer_start_time + timer_total_seconds
                )

                timer_state = "running"

                print(
                    f"Timer started: "
                    f"{format_timer(selected_seconds)}"
                )

        elif timer_state == "running":
            # Cancel the countdown and return to selection.
            timer_state = "select"
            selected_seconds = DEFAULT_TIMER_SECONDS
            timer_result_image = None

            last_encoder_position = encoder.position

            print("Timer cancelled")

        elif timer_state == "alarming":
            # Button B was pressed during the ten-second alarm.
            stop_alarm()

            print("Banana peel was thrown away")

            timer_result_image = play_result_animation(
                GOOD_RESULT_ANIMATION_PATH
            )

            timer_state = "result"

        elif timer_state == "result":
            # Reset the timer after either result.
            stop_alarm()

            timer_state = "select"
            selected_seconds = DEFAULT_TIMER_SECONDS
            timer_result_image = None

            last_encoder_position = encoder.position

            print("Timer reset")

    # Read the rotary encoder.
    encoder_position = encoder.position

    if (
        mode == "timer"
        and timer_state == "select"
        and encoder_position != last_encoder_position
    ):
        position_change = (
            encoder_position - last_encoder_position
        )

        # Each encoder step changes the timer by one second.
        selected_seconds += position_change

        # Keep the timer between one second and sixty minutes.
        selected_seconds = max(
            MIN_TIMER_SECONDS,
            min(
                MAX_TIMER_SECONDS,
                selected_seconds,
            ),
        )

        print(
            f"Timer selected: "
            f"{format_timer(selected_seconds)}"
        )

    last_encoder_position = encoder_position

    # Handle timer completion.
    current_monotonic_time = time.monotonic()

    if (
        mode == "timer"
        and timer_state == "running"
        and current_monotonic_time >= timer_end_time
    ):
        timer_state = "alarming"
        alarm_started_at = current_monotonic_time

        start_alarm()

        print(
            "Timer finished. "
            "Press B within ten seconds."
        )

    # Handle the ten-second alarm timeout.
    if (
        mode == "timer"
        and timer_state == "alarming"
        and current_monotonic_time - alarm_started_at
        >= ALARM_RESPONSE_SECONDS
    ):
        stop_alarm()

        print("Banana peel was not thrown away")

        timer_result_image = play_result_animation(
            BAD_RESULT_ANIMATION_PATH
        )

        timer_state = "result"

    last_a_pressed = a_pressed
    last_b_pressed = b_pressed

    # Clear the screen.
    draw.rectangle(
        (0, 0, width, height),
        fill=(0, 0, 0),
    )

    if mode == "clock":
        current_time_data = time.localtime()
        current_hour = current_time_data.tm_hour

        current_time = time.strftime(
            "%I:%M:%S %p",
            current_time_data,
        ).lstrip("0")

        current_date = time.strftime(
            "%b %d, %Y",
            current_time_data,
        )

        banana_index = current_hour % 12
        banana = banana_images[banana_index]

        draw.text(
            (5, 3),
            current_time,
            font=font_time,
            fill=(255, 255, 255),
        )

        draw.text(
            (5, 24),
            current_date,
            font=font_date,
            fill=(180, 180, 180),
        )

        draw.text(
            (188, 5),
            "CLOCK",
            font=font_small,
            fill=(255, 220, 0),
        )

        banana_x = (width - banana.width) // 2
        banana_y = 43

        image.paste(
            banana,
            (banana_x, banana_y),
        )

        draw.text(
            (8, 113),
            "A: CLOCK",
            font=font_small,
            fill=(0, 255, 120),
        )

        draw.text(
            (150, 113),
            "B: TIMER",
            font=font_small,
            fill=(100, 100, 100),
        )

    elif mode == "timer":
        if timer_state == "select":
            # Display the selected duration in the center.
            timer_text = format_timer(selected_seconds)

            draw.text(
                (width // 2, height // 2),
                timer_text,
                font=font_timer,
                fill=(255, 255, 255),
                anchor="mm",
            )

        elif timer_state == "running":
            current_timer_time = time.monotonic()

            remaining_seconds = max(
                0.0,
                timer_end_time - current_timer_time,
            )

            display_seconds = math.ceil(
                remaining_seconds
            )

            elapsed_seconds = (
                current_timer_time - timer_start_time
            )

            # Divide the countdown into twelve sections.
            timer_banana_index = int(
                elapsed_seconds
                * 12
                / timer_total_seconds
            )

            timer_banana_index = max(
                0,
                min(11, timer_banana_index),
            )

            countdown_text = format_timer(
                display_seconds
            )

            draw.text(
                (5, 3),
                countdown_text,
                font=font_time,
                fill=(255, 255, 255),
            )

            timer_banana = banana_images[
                timer_banana_index
            ]

            timer_banana_x = (
                width - timer_banana.width
            ) // 2

            timer_banana_y = (
                height - timer_banana.height
            ) // 2

            image.paste(
                timer_banana,
                (timer_banana_x, timer_banana_y),
            )

        elif timer_state == "alarming":
            # Keep the finished timer screen visible.
            draw.text(
                (5, 3),
                "00:00",
                font=font_time,
                fill=(255, 255, 255),
            )

            final_banana = banana_images[11]

            final_banana_x = (
                width - final_banana.width
            ) // 2

            final_banana_y = (
                height - final_banana.height
            ) // 2

            image.paste(
                final_banana,
                (final_banana_x, final_banana_y),
            )

        elif timer_state == "result":
            # Keep the final animation frame visible.
            if timer_result_image is not None:
                image.paste(
                    timer_result_image,
                    (0, 0),
                )

        # Keep the Timer interface labels visible.
        draw.text(
            (188, 5),
            "TIMER",
            font=font_small,
            fill=(255, 220, 0),
        )

        draw.text(
            (8, 113),
            "A: CLOCK",
            font=font_small,
            fill=(100, 100, 100),
        )

        draw.text(
            (150, 113),
            "B: TIMER",
            font=font_small,
            fill=(0, 255, 120),
        )

    display.image(image, rotation)
    time.sleep(0.05)