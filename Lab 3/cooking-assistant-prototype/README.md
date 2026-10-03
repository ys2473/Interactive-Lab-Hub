# Cooking Assistant Prototype

This is a standalone Raspberry Pi prototype based on Yan's tomato-pasta and
steak dialogue scripts. There is no separate phone or laptop controller. One
physical button begins or restarts the dialogue, another ends it, and all
recipe choices and commands in between are spoken by the participant.

## What satisfies the assignment

- **Raspberry Pi:** runs speech recognition, dialogue logic, timers, display,
  buttons, and text-to-speech.
- **Sensors:** a USB microphone senses speech; two GPIO push buttons sense the
  participant's START and END actions.
- **Required speech:** after pressing START, the participant must speak to
  select a recipe and continue through every recipe step.
- **System display:** the MiniPiTFT directly shows listening/thinking/speaking
  status, the current recipe step, available commands, and countdown timers.
- **Physical controller:** the START and END buttons are the controller shown
  in the controller documentation video.

## Put it in the Lab 3 repository

Place this folder here:

```text
Interactive-Lab-Hub/Lab 3/cooking-assistant-prototype/
```

The program expects these files created by the existing Lab 3 setup:

```text
Lab 3/models/silero_vad.onnx
Lab 3/voices/en_US-lessac-medium.onnx
```

## Screen and buttons

The program uses the same MiniPiTFT code and pins as Lab 2:

- Button A on GPIO 23: START or restart
- Button B on GPIO 24: END
- Display backlight: GPIO 22
- Display CS: GPIO 5
- Display DC: GPIO 25

The buttons use internal pull-ups and read LOW when pressed. No additional
buttons or wiring are required.

Install the Lab 2 display libraries into the Lab 3 virtual environment once:

```bash
cd ~/Interactive-Lab-Hub/Lab\ 3
source .venv/bin/activate
pip install -r ../Lab\ 2/requirements.txt
```

## Run

```bash
cd ~/Interactive-Lab-Hub/Lab\ 3/cooking-assistant-prototype
sudo systemctl stop piscreen.service --now
chmod +x run.sh
./run.sh
```

Stopping `piscreen.service` is required because the Lab 2 status program uses
the same screen and buttons. The cooking-assistant program draws directly on
the MiniPiTFT; Chromium and a network connection are not required.

For filming, make every recipe timer last 10 seconds while keeping the spoken
recipe durations unchanged:

```bash
./run.sh --demo-timers
```

Use `Ctrl+C` in the terminal to stop the whole program.

## Interaction

1. Press the physical START button.
2. The Pi asks what Yan wants to cook.
3. Say `Tomato pasta` or `Steak`.
4. Continue with the commands shown on screen, including `Start cooking`,
   `Next`, `Repeat`, `Go back`, `Yes`, `No`, and spoken timer durations.
5. Press the physical END button at any time to end the interaction.
6. Press START again to restart from recipe selection.

## Recording plan

1. **System video:** show the participant pressing START, speaking to the Pi,
   MiniPiTFT status changes, timer, and spoken response.
2. **Controller video or close-up:** show the two physical START/END buttons,
   their GPIO connections, and how each changes the system state. No separate
   web controller is used.
