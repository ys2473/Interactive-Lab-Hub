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

# Negating the value makes clockwise rotation positive.
last_encoder_position = -encoder.position


# Program state
mode = "clock"

last_a_pressed = False
last_b_pressed = False

a_press_started = None
a_long_press_handled = False

LONG_PRESS_SECONDS = 1.5


# Timer state
selected_minutes = 5

# Timer state can be "select", "running", or "finished".
timer_state = "select"

timer_start_time = 0.0
timer_end_time = 0.0
timer_total_seconds = 0


# File locations
BASE_DIR = Path(__file__).resolve().parent
ANIMATION_PATH = BASE_DIR / "banana-animation-2s-once.gif"


# Load and resize all twelve banana images.
banana_images = []

for image_number in range(1, 13):
    image_path = BASE_DIR / f"banana_{image_number:02d}.png"
    banana = Image.open(image_path).convert("RGB")

    # Remove unnecessary black space around the banana.
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

    # Resize the banana while preserving its proportions.
    banana.thumbnail(
        (159, 73),
        Image.Resampling.LANCZOS,
    )

    banana_images.append(banana)


def play_banana_animation():
    """Play the banana animation once using its saved frame timing."""
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

    # Play the animation after Button A is held long enough.
    if (
        a_pressed
        and a_press_started is not None
        and not a_long_press_handled
        and time.monotonic() - a_press_started
        >= LONG_PRESS_SECONDS
    ):
        print("Playing banana animation")
        play_banana_animation()

        # Show the centered current time and date.
        show_centered_datetime()

        # Speak the current time.
        announce_current_time()

        # Return to clock mode.
        mode = "clock"
        print("Clock mode")

        a_long_press_handled = True

    # A short press selects clock mode.
    if not a_pressed and last_a_pressed:
        if not a_long_press_handled:
            mode = "clock"
            print("Clock mode")

        a_press_started = None
        a_long_press_handled = False

    # Button B controls timer mode.
    if b_pressed and not last_b_pressed:
        if mode != "timer":
            # The first press enters timer selection mode.
            mode = "timer"
            timer_state = "select"
            selected_minutes = 5

            # Ignore rotations made before entering timer mode.
            last_encoder_position = encoder.position

            print("Timer selection mode")

        elif timer_state == "select":
            # The second press starts the countdown.
            timer_total_seconds = selected_minutes * 60
            timer_start_time = time.monotonic()
            timer_end_time = (
                timer_start_time + timer_total_seconds
            )
            timer_state = "running"

            print(
                f"Timer started: "
                f"{selected_minutes} minutes"
            )

        elif timer_state == "finished":
            # Press B after completion to return to selection.
            timer_state = "select"
            selected_minutes = 5
            last_encoder_position = encoder.position

            print("Timer selection mode")

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

        # Each encoder step changes the timer by one minute.
        selected_minutes += position_change

        # Keep the timer between one and sixty minutes.
        selected_minutes = max(
            1,
            min(60, selected_minutes),
        )

        print(
            f"Timer selected: "
            f"{selected_minutes} minutes"
        )

    # Always store the latest encoder position.
    last_encoder_position = encoder_position

    # Store the latest button states.
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

        # Select one banana image for each hour.
        banana_index = current_hour % 12
        banana = banana_images[banana_index]

        # Display the current time.
        draw.text(
            (5, 3),
            current_time,
            font=font_time,
            fill=(255, 255, 255),
        )

        # Display the current date.
        draw.text(
            (5, 24),
            current_date,
            font=font_date,
            fill=(180, 180, 180),
        )

        # Display the current mode.
        draw.text(
            (188, 5),
            "CLOCK",
            font=font_small,
            fill=(255, 220, 0),
        )

        # Center the banana in the lower display area.
        banana_x = (width - banana.width) // 2
        banana_y = 43

        image.paste(
            banana,
            (banana_x, banana_y),
        )

        # Show button labels only in clock mode.
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

        # Current mode in the top-right corner
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

        if timer_state == "select":
            # Display only the selected duration in the center.
            timer_text = f"{selected_minutes:02d}:00"

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

            if remaining_seconds <= 0:
                # Keep the final banana visible at zero.
                timer_state = "finished"
                display_seconds = 0
                timer_banana_index = 11

                print("Timer finished")

            else:
                # Round upward to begin at the selected time.
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

            remaining_minutes = display_seconds // 60
            remaining_remainder = display_seconds % 60

            countdown_text = (
                f"{remaining_minutes:02d}:"
                f"{remaining_remainder:02d}"
            )

            # Display the countdown in the top-left corner.
            draw.text(
                (5, 3),
                countdown_text,
                font=font_time,
                fill=(255, 255, 255),
            )

            # Display the current banana stage in the center.
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

        elif timer_state == "finished":
            # Display zero in the top-left corner.
            draw.text(
                (5, 3),
                "00:00",
                font=font_time,
                fill=(255, 255, 255),
            )

            # Keep the final banana visible in the center.
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

    display.image(image, rotation)
    time.sleep(0.05)