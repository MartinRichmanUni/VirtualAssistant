import datetime
import io
import openai
import os
import pvcobra
import pvleopard
import pvporcupine
import pyaudio
import random
import struct
import sys
import textwrap
import threading
import time

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

from colorama import Fore, Style
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
from pvleopard import *
from pvrecorder import PvRecorder
from threading import Thread, Event
from time import sleep

# Configuration and API keys
audio_stream = None
cobra = None
pa = None
porcupine = None
recorder = None
wav_file = None
last_activity_time = time.time()
inactivity_timeout = 10  # Time (in seconds) before assistant returns to idle if no input

GPT_model = "gpt-4"
openai.api_key = "REPLACE_WITH_OPENAI_API_KEY"
pv_access_key= "REPLACE_WITH_PICOVOICE_ACCESS_KEY"

client = OpenAI(api_key=openai.api_key)

# Assistant's initial persona and prompt memory
chat_log = [
    {"role": "system", "content": "Your name is Grok. You should act as a friend and use a casual tone when speaking, being brief in conversations for the most part. You should not acknowledge that you are AI."},
]

# Randomized wake responses, can be changed to suit your preference
prompt = [
    "How may I assist you?",
    "How may I help?",
    "What can I do for you?",
    "Ask me anything.",
    "Yes?",
    "I'm here.",
    "I'm listening.",
    "What would you like me to do?"
]

def append_clear_countdown():
    """
    Clears the conversation memory after a fixed duration to prevent context overload.
    """
    sleep(180)
    global chat_log
    chat_log.clear()
    chat_log = [
        {"role": "system", "content": "Your name is Grok. You should act as a friend and use a casual tone when speaking, being brief in conversations for the most part. You should not acknowledge that you are AI."},
    ]
    global count
    count = 0
    t_count.join()


def ChatGPT(query):
    """
    Sends user's spoken query to OpenAI Chat API and returns the assistant's reply.

    Args:
        query (str): The spoken input from the user.

    Returns:
        str: The assistant's response.
    """
    user_query = [{"role": "user", "content": query}]
    send_query = chat_log + user_query

    response = client.chat.completions.create(
        model=GPT_model,
        messages=send_query
    )

    answer = response.choices[0].message.content
    chat_log.append({"role": "assistant", "content": answer})
    return answer


def detect_silence():
    """
    Monitors microphone input and detects end of user's speech by checking for a period of silence
    """
    cobra = pvcobra.create(access_key=pv_access_key)
    silence_pa = pyaudio.PyAudio()
    cobra_audio_stream = silence_pa.open(
        rate=cobra.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=cobra.frame_length
    )

    last_voice_time = time.time()

    while True:
        cobra_pcm = cobra_audio_stream.read(cobra.frame_length)
        cobra_pcm = struct.unpack_from("h" * cobra.frame_length, cobra_pcm)

        if cobra.process(cobra_pcm) > 0.2:
            last_voice_time = time.time()
        else:
            silence_duration = time.time() - last_voice_time
            if silence_duration > 1.3:
                print("End of query detected\n")
                cobra_audio_stream.stop_stream()
                cobra_audio_stream.close()
                cobra.delete()
                break


def listen():
    """
    Waits for user's voice input after wake word. If no voice is detected within
    `inactivity_timeout`, the assistant returns to idle.
    """
    cobra = pvcobra.create(access_key=pv_access_key)
    listen_pa = pyaudio.PyAudio()

    listen_audio_stream = listen_pa.open(
        rate=cobra.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=cobra.frame_length
    )

    print("Listening...")
    start_time = time.time()

    while True:
        cobra_pcm = listen_audio_stream.read(cobra.frame_length)
        cobra_pcm = struct.unpack_from("h" * cobra.frame_length, cobra_pcm)

        if cobra.process(cobra_pcm) > 0.3:
            print("Voice detected")
            global last_activity_time
            last_activity_time = time.time()
            break

        if time.time() - start_time > inactivity_timeout:
            break

    listen_audio_stream.stop_stream()
    listen_audio_stream.close()
    cobra.delete()


def responseprinter(chat):
    """
    Prints the assistant's response with a typewriter animation.

    Parameter:
        chat (str): Assistant's response.
    """
    wrapper = textwrap.TextWrapper(width=100) # Can be adjusted to preference
    paragraphs = chat.split('\n')
    wrapped_chat = "\n".join([wrapper.fill(p) for p in paragraphs])
    for word in wrapped_chat:
        time.sleep(0.055)
        print(word, end="", flush=True)
    print()


def voice(chat):
    """
    Converts the assistant's text response to speech using OpenAI Text-to-Speech and plays it.

    Parameter:
        chat (str): Text to be spoken.
    """
    response = client.audio.speech.create(
        model="tts-1",
        voice="echo", # Various voices are available, use https://www.openai.fm/ to find a voice that suits your preference
        input=chat
    )
    response.stream_to_file("speech.mp3")

    pygame.mixer.init()
    pygame.mixer.music.load("speech.mp3")
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pass
    sleep(0.2)


def wake_word():
    """
    Listens for the wake word defined in a custom Porcupine model.
    Once detected, assistant starts interaction loop.
    """
    porcupine = pvporcupine.create(
        keyword_paths=['grok.ppn'], # Filepath for custom wake word file generated using https://console.picovoice.ai/
        access_key=pv_access_key,
        sensitivities=[0.1]
    )

    # Suppress Porcupine error messages
    devnull = os.open(os.devnull, os.O_WRONLY)
    old_stderr = os.dup(2)
    sys.stderr.flush()
    os.dup2(devnull, 2)
    os.close(devnull)

    wake_pa = pyaudio.PyAudio()

    porcupine_audio_stream = wake_pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )

    while True:
        porcupine_pcm = porcupine_audio_stream.read(porcupine.frame_length)
        porcupine_pcm = struct.unpack_from("h" * porcupine.frame_length, porcupine_pcm)

        if porcupine.process(porcupine_pcm) >= 0:
            print(Fore.GREEN + "\nWake word detected\n" + Style.RESET_ALL)
            porcupine_audio_stream.stop_stream()
            porcupine_audio_stream.close()
            porcupine.delete()
            os.dup2(old_stderr, 2)
            os.close(old_stderr)
            break


class Recorder(Thread):
    """
    Handles continuous audio recording in a separate thread using Picovoice Recorder.
    """
    def __init__(self):
        super().__init__()
        self._pcm = []
        self._is_recording = False
        self._stop = False

    def is_recording(self):
        return self._is_recording

    def run(self):
        self._is_recording = True
        recorder = PvRecorder(device_index=-1, frame_length=512)
        recorder.start()

        while not self._stop:
            self._pcm.extend(recorder.read())

        recorder.stop()
        self._is_recording = False

    def stop(self):
        self._stop = True
        while self._is_recording:
            pass
        return self._pcm

try:
    o = create(access_key=pv_access_key)
    event = threading.Event()
    count = 0

    while True:
        try:
            wake_word()  # Wait for user to say custom keyword ("Hey Grok")
            voice(random.choice(prompt))  # Assistant responds to wake word

            while True:
                recorder = Recorder()
                recorder.start()

                listen()  # Wait for speech
                detect_silence()  # Detect end of query

                if time.time() - last_activity_time > inactivity_timeout: # Returns assistant to idle
                    print(Fore.YELLOW + "\nInactivity timeout reached. Waiting for wake word...\n" + Style.RESET_ALL)
                    break

                transcript, words = o.process(recorder.stop())
                recorder.stop()
                print("You said: " + transcript)

                res = ChatGPT(transcript)
                print("\nGrok's response is:\n")
                t1 = threading.Thread(target=voice, args=(res,))
                t2 = threading.Thread(target=responseprinter, args=(res,))
                t1.start()
                t2.start()
                t1.join()
                t2.join()

            event.set()
            recorder.stop()
            o.delete
            recorder = None

        except openai.APIError as e:
            print("\nThere was an API error. Please try again in a few minutes.")
            voice("\nThere was an API error. Please try again in a few minutes.")
            event.set()



        except openai.RateLimitError as e:
            print("\nYou have hit your assigned rate limit.")
            voice("\nYou have hit your assigned rate limit.")
            event.set()       
            recorder.stop()
            o.delete
            recorder = None
            break

        except openai.APIConnectionError as e:
            print("\nI am having trouble connecting to the API.  Please check your network connection and then try again.")
            voice("\nI am having trouble connecting to the A P I.  Please check your network connection and try again.")
            event.set()       
            recorder.stop()
            o.delete
            recorder = None
            sleep(1)

        except openai.AuthenticationError as e:
            print("\nYour OpenAI API key or token is invalid, expired, or revoked.  Please fix this issue and then restart my program.")
            voice("\nYour Open A I A P I key or token is invalid, expired, or revoked.  Please fix this issue and then restart my program.")
            event.set()       
            recorder.stop()
            o.delete
            recorder = None
   
except KeyboardInterrupt:
    print("\nExiting ChatGPT Virtual Assistant")
    o.delete
