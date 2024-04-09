# Voice Chat GPT

Voice chat GPT is an experiment in integrating a local voice to text tool
(whisper), with groq's API for fast querying of LLMs. The tools is designed
to record audio through the microphone, save it as a WAV file, transcribe
it locally and send a request to groq’s api that in turn returns an answer.

## Dependencies

The application has the following python dependencies:

- pyaudio
- watchdog
- pynput
- OpenAI Whisper
- groq
- dotenv

Install them using:

```bash

pip install pyaudio watchdog pynput groq openai-whisper python-dotenv

```

## Features

- **Audio Recording**: Start and stop audio recording using a keyboard shortcut
  (right ctrl) and save it as a WAV file.
- **File Monitoring**: A background daemon monitors for changes to the audio
  file and transcribes it using whisper as soon as it detects any changes.
- **Transcribing using Whisper**: Transcribes the audiofile locally. If the
  model is not yet downloaded whisper
  will download the model for you on first run.
- **Upload to groq API**: Uploads the file to groq. You are able to configure
  what model to use, currently uses the 'base' model, a system message to
  initialise the model and how many of your previous questions you want to
  resend to the model.
  It currently sends the last 5 questions and answers to the model for context.
- **Upload to Elven Labs**: Uploads the text reply to Eleven labs and converts
  the text to speech using their models. Plays the audio file back to the user.

## Running the application

```bash

./voice_chat_gpt.py

```
