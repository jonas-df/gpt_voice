#!/usr/bin/python3

from pynput import keyboard
import pyaudio
import wave
from threading import Event, Thread
import sys
from watchdog.events import FileSystemEventHandler
import os
import time
from watchdog.observers import Observer
import whisper
from groq import Groq
from dotenv import load_dotenv
import json

# import eleven_api
import pygame
import edge_api


# Define the format, channels, rate, and chunk size for recording
FORMAT = pyaudio.paInt16
CHANNELS = 1 if sys.platform == "darwin" else 2
RATE = 44100
CHUNK = 1024
WAVE_OUTPUT_FILENAME = "output.wav"
GREEN = "\033[32m"  # Green text
YELLOW = "\033[33m"  # Yellow text
RESET = "\033[0m"
TEXT_FILENAME = "transcribe_log.txt"
MESSAGES_JSON = "message.json"

audio = pyaudio.PyAudio()

# Initialize the stream and recording state
stream = None
recording_data = None
start_recording_flag = Event()
stop_recording_flag = Event()
recording_thread = None

# Load groq API credentials stored in .env file
load_dotenv()

# Instantiate the tts

# tts = eleven_api.ElevenLabsTTS()


# JSON helper functions
def append_json(file_path, role, content):
    initial_message = {
        "role": "system",
        "content": "You are a helpful assistant. You give concise answers of a maximum of 15 lines.",
    }

    try:
        with open(file_path, "r") as file:
            messages = json.load(file)
    except FileNotFoundError:
        messages = []

    # Ensure the initial message is always at the beginning, before any new messages are added
    if not messages or messages[0].get("content") != initial_message.get("content"):
        messages = [initial_message] + messages

    # Append the new message
    messages.append({"role": role, "content": content})

    # Maintain a rolling window of the last i messages, ensuring the initial message is included
    if len(messages) > 11:
        messages = [initial_message] + messages[-10:]

    # Write the updated list back to the file
    with open(file_path, "w") as file:
        json.dump(messages, file, indent=4)


def read_json(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


# File helper functions
def write_to_file(message, file_path):
    with open(file_path, "w") as file:
        file.write(message)


def append_to_file(message, file_path):
    with open(file_path, "a") as file:
        file.write(message + "\n\n")


def read_file(file_path):
    with open(file_path, "r") as file:
        content = file.read()
    return content


def record_audio():
    global stream, recording_data
    start_recording_flag.wait()
    frames = []
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True)

    while not stop_recording_flag.is_set():
        data = stream.read(CHUNK)
        frames.append(data)
    print("Done recording...")

    stream.close()

    recording_data = b"".join(frames)

    print("Saving...")
    with wave.open("output.wav", "wb") as sound_file:
        sound_file.setnchannels(CHANNELS)
        sound_file.setsampwidth(audio.get_sample_size(FORMAT))
        sound_file.setframerate(RATE)
        sound_file.writeframes(b"".join(frames))
        sound_file.close()
    print("Finished saving... \n")
    start_recording_flag.clear()
    stop_recording_flag.clear()


def button_pressed(key):
    global recording_thread
    if key == keyboard.Key.ctrl_l and not start_recording_flag.is_set():
        start_recording_flag.set()
        stop_recording_flag.clear()
        recording_thread = Thread(target=record_audio)
        recording_thread.start()
        print("Key pressed, starting recording...")


def button_release(key):
    if key == keyboard.Key.ctrl_l:
        stop_recording_flag.set()
        print("Key released, stopping recording... ")


# Functions to handle listening for keyboard input and watching for file changes
def start_listener():
    with keyboard.Listener(
        on_press=button_pressed, on_release=button_release
    ) as listener:
        listener.join()


class FileMonitorHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_modified = time.time()

    def on_modified(self, event):
        if event.src_path.endswith(WAVE_OUTPUT_FILENAME):
            current_time = time.time()
            # Ignore events that occur within 1 second of the last one
            if current_time - self.last_modified > 1:
                print(f"File {event.src_path} has been modified.\n")
                Thread(
                    target=transcribe_audio,
                    args=(WAVE_OUTPUT_FILENAME,),
                    kwargs={"callback": on_decode_audio_complete},
                ).start()
                self.last_modified = current_time


def start_watcher():
    path_to_watch = os.path.dirname(os.path.abspath(WAVE_OUTPUT_FILENAME))
    print(f"\n Path to watch {path_to_watch}")
    event_handler = FileMonitorHandler()
    observer = Observer()
    observer.schedule(event_handler, path=path_to_watch, recursive=False)
    observer.start()
    print(f"Watching {path_to_watch} for changes")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()


def start_watcher_daemon():
    Thread(target=start_watcher, daemon=True).start()


# Transcribing audio to text using whisper
def transcribe_audio(track, model="base", lang="en", callback=None):
    try:
        decode_model = whisper.load_model(model)
    except Exception as e:
        return f"Failed to load whisper model...'{model}': {e}"

    try:
        audio = whisper.load_audio(track)
        audio = whisper.pad_or_trim(audio)
    except Exception as e:
        return f"Failed to load audio'{model}': {e}"

    # make log-Mel spectrogram and move to the same device as the model
    mel = whisper.log_mel_spectrogram(audio).to(decode_model.device)

    try:
        options = whisper.DecodingOptions(language=lang, fp16=False)
        result = whisper.decode(decode_model, mel, options)

    except Exception as e:
        return f"Failed to transcribe the audio...'{model}': {e}"

    message = result.text  # pyright: ignore List[DecodingResult]
    success_message = f"Transcribed text: {message} \n"
    print(f"{GREEN}{success_message}{RESET}")
    write_to_file(message, TEXT_FILENAME)
    append_json(MESSAGES_JSON, "user", message)

    if callback:
        callback()


def on_decode_audio_complete():
    groq_post_question()


def play_mp3(file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():  # Wait for audio to finish playing
        pygame.time.Clock().tick(10)


def groq_post_question():

    client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
    )

    chat_completion = client.chat.completions.create(
        messages=read_json(MESSAGES_JSON),
        model="mixtral-8x7b-32768",
    )

    reply = chat_completion.choices[0].message.content

    print(f"{YELLOW}{reply}{RESET} \n")
    append_json(MESSAGES_JSON, "assistant", reply)

    edge_api.EdgeTTS.run(reply, "en-GB-SoniaNeural", "output.mp3")
    # tts.text_to_speech(reply)
    play_mp3("output.mp3")


if __name__ == "__main__":
    start_watcher_daemon()
    start_listener()
