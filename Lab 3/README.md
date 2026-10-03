# Chatterboxes -- Yan Shen(ys2473)

# Part 1

## A. Text to Speech

I chose the Piper voice for my greeting because it sounds more natural and pleasant.

Different voices does not feel like the same greeting. The eSpeak voice sounds like a robot and the voice sounds like a machine notification. In comparison, the Piper voice is more fluent and have human rhythm, so the greeting is more friendly.

## B. Speech to Text

<img width="738" height="368" alt="Codex Image Sep 27, 2026, 04_13_04 PM" src="https://github.com/user-attachments/assets/498a7ec2-030b-405f-a055-93f44ea30982" />

I recorded a audio clip saying “It’s Sunday, September 27th.”

tiny.en: The transcript was “It’s Sunday, September 27th.” real-time factor: 0.20x, transcription took 1.01 seconds.

base.en: The transcript was “It’s Sunday September the 27th.” real-time factor: 0.41x, transcription took 2.03 seconds.

Both models correctly understood the sentences. The base model generates more natural wording, but it takes longer, approximately twice as long as the other one. I would choose tiny.en for a responsive dialogue system. When recognizing more difficult speech or numeric base.en might be more preferable.

## C. Turn-taking: knowing when someone has stopped talking

I tested three endpointing thresholds: 0.2 seconds, 0.7 seconds, and 1.5 seconds.

0.2 seconds: It split my sentence into two parts. it transcribe the second part of my sentence wrong. And seems like it's unpatient.

1.5 seconds: the complete sentence was transcribed correctly. but it delays more than the 0.2s one.

0.7 second: provide a better balance and correctly transcribe my words.


<img width="657" height="214" alt="Screenshot 2026-09-27 at 4 47 46 PM" src="https://github.com/user-attachments/assets/d2bef412-e1fa-44d0-bddd-c4c84b9177cb" />


## D. Storyboard

What I want to design is a cooking timer with built-in recipes.

The main voice-controlled functions of this cooking timer are divided into several steps: selecting recipes, checking ingredients, cooking steps and managing the timer. It only gives one cooking instruction at a time until the user provides a clear instruction such as "next". These simple instructions are very easy to recognize. For these easy commands, I usually give 0.7s to wait for slience. If some instructions need time for user to check, then 2s of wait will be set.

At present, there is only a recipe for tomato pasta. More options can be imported later.

<img width="2364" height="1365" alt="IMG_2151" src="https://github.com/user-attachments/assets/e49165a3-a14c-4ecb-a41c-aff99303230d" />




dialogue：

Device: “Hi Yan! What would you like to cook today?” (wait for 0.7s of slience)

User: “pasta.”

Device: “You will need pasta, tomato sauce, garlic, olive oil, salt, and water. Say ‘repeat’ to hear the ingredients again, or say ‘start cooking’ when you are ready.” (wait for 2s of slience)

User: “Start cooking.”

Device: “Step one: Fill a pot with water and place it on the stove. Say ‘next’ when the water begins to boil.” (Wait until the user says a command like "next".)

User: “Next.”

Device: “Step two: Add the pasta to the pot. How many minutes do you want for the pasta?” (wait for 0.7 of slience)

User: “Fifteen minutes.”

Device: “You said fifteen minutes?” (wait for 0.7s of slience)

User: “Yes.”

Device: “Okay. I have started a fifteen-minute timer. Now, you can heat the tomato sauce with garlic and olive oil.” (wait for the timer finishes)

Device: “Yan, it's already fifteen minutes. Drain the pasta and mix it with the tomato sauce.” (wait until next command)

User: “Next.”

Device: “Your tomato pasta is ready. Enjoy your meal!”



## E. Acting out the dialogue

https://youtu.be/5As__L0jLFQ

This conversation basically went as expected because I set very clear instructions. However, this might affect the richness of user experience, and the functions are very limited. More instructions need to be added later to make this device more practical.


---

# Lab 3 Part 2

## Prep for Part 2

1. What are concrete things that could use improvement in the design of your device? For example: wording, timing, anticipation of misunderstandings.
   
     Provide more recipe choices: The current prototype supports only one recipe. I would add one or two additional recipes (easy to achieve for now) so that users can choose what they want to cook.

     Confirm numerical information: Speech recognition may confuse similar numbers, such as “fifteen” and “fifty.” Before starting a timer, the device should display the recognized time on the screen and ask the user to confirm it.
    
     Add more voice commands: The system should support commands such as “repeat,” “go back,” and “stop.” These commands would allow users to control the recipe without touching the device.
    
     Explain the available commands: The screen should display the commands that users can say, so they do not have to guess how to interact with the system.

     Handle silence: If the device does not detect a response for an extended period, it should remind the user or repeat the question instead of waiting indefinitely.

     If the device cannot understand the user, it should clearly explain the problem ("Sorry I cannot understand.") and ask again. 
   
2. What are other modes of interaction *beyond speech* that you might also use to clarify how to interact? In particular: how does someone know when the device is listening, and when it is thinking? You have a screen and an LED.

      The redesigned device will use a screen, an LED, a microphone, a speaker, and two physical buttons.
      
      Screen: When no recipe is active, the default screen will display the available starting commands, such as “Choose Recipe” and “Start Cooking.” During a recipe, the screen will display commands 
      relevant to the current situation, such as “Next,” “Repeat,” “Go Back,” and “Stop.” If the information requires multiple pages, the user can use two physical buttons to move to the previous or next page. The screen will also display status messages such as “Listening…” and “Thinking…”. The timer will also show on the screen.
      
      LED: The LED will provide immediate feedback about the device’s current state. It will remain steadily lit while the user is speaking, indicating that the device is listening. It will blink slowly while the device is recognizing or processing the user’s speech.
      
      Microphone: The microphone will capture the user’s speech for voice-command recognition.

      Speaker: The speaker will read recipe instructions aloud, ask questions, confirm recognized information, and tell the user when the system does not understand a command.
   
3. Make a new storyboard, diagram and/or script based on these reflections.

   SCRIPT 1 — TOMATO PASTA
      
      Device: “Hi Yan! What would you like to cook today?”
   (The screen displays “Tomato pasta” and “Steak.”“Go Back,” and “Stop.”)
   (Wait for the user’s response, followed by 0.7 seconds of silence.)
      
      User: “Pasta.”
   (The LED stays on throughout the user’s speech, then slowly blinks while the device recognizes the response. It turns off when the device begins speaking.)
      
      Device: “You will need pasta, tomato sauce, garlic, olive oil, salt, and water. Say ‘repeat’ to hear the ingredients again, or say ‘start cooking’ when you are ready.”
   (The screen displays “Repeat” “Start cooking” “Go Back,” and “Stop.” The LED remains off.)
   (Wait for the user’s response, followed by 2 seconds of silence.)
      
      User: “Start cooking.”
   (The LED stays on during speech, then slowly blinks during recognition.)
      
      Device: “Step one: Fill a pot with water, add salt, and place it on the stove. Say ‘next’ when the water begins to boil, or say ‘repeat’ to hear this step again.”
   (The screen displays “Next” and “Repeat.”“Go Back,” and “Stop.”)
   (Wait for a command, followed by 0.7 seconds of silence.)
      
      User: “Next.”
   (The LED stays on during speech, then slowly blinks during recognition.)
      
      Device: “Step two: Add the pasta to the pot. How many minutes would you like to set for the pasta?”
   (Wait for the user’s response, followed by 0.7 seconds of silence.)
      
      User: “Fifteen minutes.”
   (The LED stays on during speech, then slowly blinks during recognition.)
      
      Device: “You said fifteen minutes. Is that correct?”
   (The LED turns off. The screen displays “15:00” with “Yes” and “No.” The timer has not started.)
   (Wait for the user’s response, followed by 0.7 seconds of silence.)
      
      User: “Yes.”
   (The LED stays on during speech, then slowly blinks during recognition.)
      
      Device: “Okay. I have started a fifteen-minute timer. Meanwhile, heat the tomato sauce with garlic and olive oil in a separate pan.”
   (The screen displays the running countdown.)
   (Wait until the timer finishes.)
      
      Device: “Yan, your fifteen-minute timer is finished. Check the pasta. If it is ready, drain it and mix it with the tomato sauce. Say ‘next’ when you are done, ‘add time’ if it needs longer, or ‘repeat’ to hear this step again.” (The screen displays “Next,” “Add time,” and “Repeat.” The LED remains off.)
   (Wait for a command, followed by 0.7 seconds of silence.)
      
      User: “Next.”
   (The LED stays on during speech, then slowly blinks during recognition.)
      
      Device: “Your tomato pasta is ready. Enjoy your meal!”
   (The LED turns off. The screen displays ‘Pasta ready. Enjoy!')

If no response is detected for five seconds, the device says, “I’m still waiting. Say ‘repeat’ if you would like to hear the instruction again.”

If a command is not recognized, the screen displays the recognized text and the device says, “Sorry, I didn’t understand. You can say ‘next,’ ‘repeat,’ ‘go back,’ or ‘stop.’”
   

   SCRIPT 2 — STEAK
      
   Device: “Hi Yan! What would you like to cook today?”
   (The screen displays “Tomato pasta” and “Steak.”)
   (Wait for the user’s response, followed by 0.7 seconds of silence.)
      
   User: “Steak.”
   (The LED stays on throughout the user’s speech, then slowly blinks while the device recognizes the response. It turns off when the device begins speaking.)
      
   Device: “You will need a steak, cooking oil, salt, pepper, a frying pan, tongs, and a food thermometer. Say ‘repeat’ to hear the list again, or say ‘start cooking’ when you are ready.”
   (The screen displays “Repeat” and “Start cooking.” “Go Back,” and “Stop.” The LED remains off.)
   (Wait for the user’s response, followed by 2 seconds of silence.)
      
   User: “Start cooking.”
   (The red LED stays on during speech, then slowly blinks during recognition.)
      
   Device: “Step one: Pat the steak dry and season both sides with salt and pepper. Say ‘next’ when you are ready, or say ‘repeat’ to hear this step again.”
   (The LED turns off. The screen displays “Next” and “Repeat.”“Go Back,” and “Stop.”)
   (Wait for a command, followed by 0.7 seconds of silence.)
      
   User: “Next.”
   (The LED stays on during speech, then slowly blinks during recognition.)
      
   Device: “Step two: Heat your frying pan and add a little cooking oil. Say ‘next’ when the pan is hot, or say ‘repeat’ to hear this step again.”
   (The LED turns off. The screen displays “Next” and “Repeat.”“Go Back,” and “Stop.”)
   (Wait for a command, followed by 0.7 seconds of silence.)
      
   User: “Next.”
   (The LED stays on during speech, then slowly blinks during recognition.)
      
   Device: “Step three: Carefully place the steak in the pan. How many minutes would you like to set before checking the first side?”
   (Wait for the user’s response, followed by 0.7 seconds of silence.)
      
   User: “Three minutes.”
   (The LED stays on during speech, then slowly blinks during recognition.)
      
   Device: “You said three minutes. Is that correct?”
   (The LED turns off. The screen displays “03:00” with “Yes” and “No.” The timer has not started.)
   (Wait for the user’s response, followed by 0.7 seconds of silence.)
      
   User: “Yes.”
   (The LED stays on during speech, then slowly blinks during recognition.)
      
   Device: “Okay. I have started a three-minute timer.”
   (The LED turns off. The screen displays the running countdown.)
   (Wait until the timer finishes.)
      
   Device: “Yan, your timer is finished. Check the crust and flip the steak. Say ‘next’ once you have turned it, or say ‘repeat’ to hear this step again.”
   (The screen displays “Next” and “Repeat.”“Go Back,” and “Stop.” The LED remains off.)
   (Wait for a command, followed by 0.7 seconds of silence.)
      
   User: “Next.”
   (The LED stays on during speech, then slowly blinks during recognition.)
      
   Device: “How many minutes would you like to set before checking the second side?”
   (Wait for the user’s response, followed by 0.7 seconds of silence.)
      
   User: “Three minutes.”
   (The LED stays on during speech, then slowly blinks during recognition.)
      
   Device: “You said three minutes. Is that correct?”
   (Wait for the user’s response, followed by 0.7 seconds of silence.)
      
   User: “Yes.”
   (The LED stays on during speech, then slowly blinks during recognition.)
      
   Device: “Okay. I have started another three-minute timer.”
   (The LED turns off. The screen displays the running countdown.)
   (Wait until the timer finishes.)
      
   Device: “Yan, your timer is finished. Check the center of the steak with your thermometer. Once it reaches at least 145 degrees Fahrenheit, or 63 degrees Celsius, transfer it to a plate. Say ‘start resting’ when it is on the plate, ‘add time’ if it needs more cooking, or ‘repeat’ to hear this step again.”
   (The screen displays “Start resting,” “Add time,” and “Repeat.” The LED remains off.)
   (Wait for a command, followed by 0.7 seconds of silence.)
      
   User: “Start resting.”
   (The LED stays on during speech, then slowly blinks during recognition.)
      
   Device: “Okay. Let the steak rest for at least three minutes. I have started the resting timer.”
   (The LED turns off. The screen displays the running three-minute countdown.)
   (Wait until the timer finishes.)
      
   Device: “Yan, the resting time is finished. Your steak is ready to serve. Enjoy your meal!”
   (The screen displays ‘Steak ready. Enjoy!')

## Prototype your system

### How the System Works

My prototype is a voice-controlled cooking assistant. It provides instructions for two recipes: tomato pasta and steak(can add more in the future). The system uses the two buttons to starts or stops the interaction. After Button A is pressed, the device asks the participant what they would like to cook. The participant can choose one of the recipe and the system moves to the corresponding one. The device will read the instructions to the user step by step and the user will respond using provided commands. The program then checks the recognized text for commands such as “start cooking,” “next,” “repeat,” “go back,” “stop,” “yes,” and “no.”The MiniPiTFT displays the current recipe name, step number, instruction, and available voice commands. It also displays whether the system is listening, thinking, speaking, or running a timer. The screen is also used to make sure if the time recognized is correct. When a recipe is complete, the screen displays “Enjoy your meal!” in large centered text and stops listening for speech. After five seconds, it automatically returns to the initial page. If the participant stops the interaction with Button B or the voice command “stop,” the system displays the stopped page and also returns to the initial page after five seconds without another button press.

Chose tomato pasta with different commands and stop in the end.
https://youtube.com/shorts/tBGqAAaYoB8

Chose tomato pasta in a normal process.

Chose steak in a normal process.


<img width="644" height="467" alt="Screenshot 2026-10-03 at 12 09 39 PM" src="https://github.com/user-attachments/assets/0dc627e6-7271-4313-98d5-045cd4bf8291" />



Because I was unable to figure out how to safely connect the LED to the Raspberry Pi, I did not include it in my prototype. Instead, I displayed three different system states in the upper-left corner of the screen with three different colors: “Listening,” “Thinking,” and “Speaking.”

<img width="200" height="120" alt="Screenshot 2026-10-03 at 3 48 41 PM" src="https://github.com/user-attachments/assets/f88cf985-94c6-4921-9ded-8ed2d45eb21d" />
<img width="200" height="120" alt="Screenshot 2026-10-03 at 3 48 46 PM" src="https://github.com/user-attachments/assets/ad77ff62-f073-4d13-9e1e-e27fc7b0e538" />
<img width="200" height="120" alt="Screenshot 2026-10-03 at 3 48 51 PM" src="https://github.com/user-attachments/assets/6506345f-a9f1-442e-8163-e3fd0ffe58d6" />


## Test the system

Try to get at least two people to interact with your system. (Ideally, you would inform them that there is a wizard *after* the interaction, but we recognize that can be hard.)

Answer the following:

### What worked well about the system and what didn't?

I tested the system with two participants. Both were able to choose a recipe, follow the steps, and use the timer. Displaying “Listening,” “Thinking,” and “Speaking” also helped participants understand the system’s current state. However, one of them felt that some instructions were too long. It's easy to forget the available commands or the beginning of an instruction before the device finishes speaking.  Speech recognition also had difficulty in noisy environments and sometimes confused similar-sounding words and numbers.

### What worked well about the controller and what didn't?

The two buttons on the MiniPiTFT provided a simple physical controller. Button A started or restarted the interaction, while Button B stopped it. This was easy to operate and did not require a separate computer or phone. The screen also worked as part of the controller by showing the current recipe, step, timer, available commands, and system state. However, the buttons are not clearly labeled, so a new participant may not know what Button A and Button B do without an explanation.

### What lessons can you take away from the WoZ interactions for designing a more autonomous version of the system?

The instructions should be shorter and divided into smaller pieces. Instead of presenting several actions and commands in one sentence, the system could give one instruction at a time and display only the commands that are currently relevant. An autonomous version should use the current recipe state to limit the possible interpretations of the participant’s speech. For example, when the device asks the participant to choose a recipe, it only needs to recognize “pasta” or “steak.”

### How could you use your system to create a dataset of interaction? What other sensing modalities would make sense to capture?

The system could save each interaction as a structured record containing the current recipe step, the participant’s audio, Whisper’s transcription, the command selected by the system, the participant’s response time, and whether the participant had to repeat or correct the command. It could also record timer confirmations, misunderstood commands, button presses, use of “repeat” or “go back,” and moments when no response was received. These records could help identify which instructions are too long and which words or numbers are frequently misrecognized.

