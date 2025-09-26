#!/usr/bin/env python3

import RPi.GPIO as GPIO
import json
import random
import time
import requests
# import speech_recognition as sr

maxLoopCount = 3
loopCount = 0
data_path = "data.json"
debugtext = "ik ben een testbericht"
url = "urlofyourvpsgoeshere" 

def speak(text, lang='nl'):
    from gtts import gTTS
    import os
    tts = gTTS(text=text, lang=lang)
    filename = "/tmp/tts.mp3"
    tts.save(filename)
    os.system(f"mpg123 -a alsa {filename}")



def get_microphone_index(name_substring):
    import pyaudio
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if name_substring.lower() in info["name"].lower() and info["maxInputChannels"] > 0:
            return i
    return None

def listen():
    import speech_recognition as sr
    recognizer = sr.Recognizer()
    recognizer = sr.Recognizer()

    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 3.5
    recognizer.non_speaking_duration = 0.8

    mic_index = get_microphone_index("usb")

    if mic_index is None:
        return ""

    try:
        with sr.Microphone(device_index=mic_index) as source:
            recognizer.adjust_for_ambient_noise(source, duration=2)
            audio = recognizer.listen(source, timeout=30, phrase_time_limit=30)
            return recognizer.recognize_google(audio, language="nl-NL")
    except sr.WaitTimeoutError:
        return ""
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        return ""
    except Exception as e:
        return ""

def personal():
    speak("Hallo! Ik ben koro de zorgrobot. Ik ben hier om een gezellig gesprek met u te voeren")

personal()
        
# Instructions function (spoken)
def instructions():
    speak("Om met mij te praten kan u de blauwe tag voor mijn buik houden. Wilt u uw data verwijderen? Hou dan de rode tag voor mij")

def save_answer_to_json(prompt, chat_history):
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        if item["question"] == prompt:
            item["answer"] = chat_history
            break

    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def conversation_loop(ai_response, prompt):
    global loopCount, chat_history

    speak(ai_response)

    # Save AI response into the last message in history
    if chat_history and chat_history[-1]["model"] == "":
        chat_history[-1]["model"] = ai_response

    # Save progress
    save_answer_to_json(prompt, chat_history)

    if loopCount < maxLoopCount:
        user_input = listen()

        if not user_input:
            speak("Ik heb u niet goed verstaan. Probeer zou duidelijk mogelijk te praten.")
            # Re-prompt with last AI message
            conversation_loop(ai_response, prompt)
            return

        chat_history.append({"user": user_input, "model": ""})

        payload = {
            "prompt": prompt,
            "answer": user_input,
            "history": chat_history
        }
        try:
            response = requests.post(url, json=payload)
            ai_response = response.text if response.ok else debugtext
            loopCount += 1
        except requests.RequestException as e:
            speak("Ik kan momenteel niet verbinden met de server. Probeer het later opnieuw of check de internet connectie.")
            return

        # Save AI response again (next loop)
        conversation_loop(ai_response, prompt)
    else:
        speak("Het was leuk om een praatje met u te houden. Zullen wij het ergens anders over hebben?")
        save_answer_to_json(prompt, chat_history)
        loopCount = 0
        chat_history.clear()

def convo():
    global chat_history, current_prompt, loopCount
    loopCount = 0

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    unanswered = [item for item in data if not item.get("answer")]

    if not unanswered:
        answered = [item for item in data if isinstance(item.get("answer"), list)]
        if not answered:
            speak("Ik kan mijn databank aan vragen niet vinden. Neem contact op met Carebotic.")
            return

        chosen = random.choice(answered)
        current_prompt = chosen["question"]
        chat_history = chosen["answer"]
        speak(current_prompt)

        last_user_input = chat_history[-1]["user"] if chat_history else ""
        payload = {
            "prompt": current_prompt,
            "answer": last_user_input,
            "history": chat_history
        }

        try:
            response = requests.post(url, json=payload)
            ai_response = response.text if response.ok else debugtext
        except requests.RequestException as e:
            speak("Ik kan momenteel niet verbinden met de server. Probeer het later opnieuw of check de internet connectie.")
            return

        conversation_loop(ai_response, current_prompt)

    else:
        chosen = random.choice(unanswered)
        current_prompt = chosen["question"]
        speak(current_prompt)

        user_input = listen()

        if not user_input:
            speak("Ik kan u niet horen. Kunt u wat luider en duidelijker praten?")
            return

        chat_history = [{"user": user_input, "model": ""}]
        payload = {
            "prompt": current_prompt,
            "answer": user_input,
            "history": chat_history
        }

        try:
            response = requests.post(url, json=payload)
            ai_response = response.text if response.ok else debugtext
        except requests.RequestException as e:
            speak("Ik kan momenteel niet verbinden met de server. Probeer het later opnieuw of check de internet connectie.")
            return

        # Save after initial question is answered
        if chat_history and chat_history[-1]["model"] == "":
            chat_history[-1]["model"] = ai_response
        save_answer_to_json(current_prompt, chat_history)

        conversation_loop(ai_response, current_prompt)

# Handle delete command
def delete_file():
    import os
    global data_path
    if os.path.exists(data_path):
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            item["answer"] = []

        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        speak("Alle persoonlijke data is succesvol verwijderd.")
    else:
        speak("Alle persoonlijke data is al verwijderd.")

# RFID reader with timeout
def read_rfid_with_timeout(timeout=30):
    from mfrc522 import SimpleMFRC522
    reader = SimpleMFRC522()
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            id, text = reader.read_no_block()
            if text:
                return text.strip()
        except Exception:
            continue
        time.sleep(0.5)
    return None

def social_reminder():
    if random.randint(1, 3) == 1:
        speak("praten met mij kan natuurlijk heel gezellig zijn, maar het is ook belangrijk om sociaal contact te zoeken om u heen. Misschien is het een idee om met iemand om u heen te praten in plaats van mij? Als u toch met mij wilt praten, houd dan de bluwe tag voor mijn buik.")

# Main loop
def main_loop():
    try:
        while True:
            instructions()
            social_reminder()
            scanned_data = read_rfid_with_timeout(30)

            if scanned_data.lower() == "helloworld":
                convo()
            elif scanned_data.lower() == "delete":
                delete_file()
            else:
                speak("Er is iets mis met het scannen van de tag. Probeer het opnieuw.")
    finally:
        GPIO.cleanup()

# Entry point
if __name__ == "__main__":
    main_loop()
