#!/usr/bin/python3

from dotenv import load_dotenv
import os
import requests


class ElevenLabsTTS:
    def __init__(self):
        load_dotenv()

        self.chunk_size = 1024
        self.url = "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM"  # voice_id_string
        self.headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": os.getenv("ELEVEN_API_KEY"),
        }

    def text_to_speech(
        self,
        text,
        model_id="eleven_monolingual_v1",
        stability=0.5,
        similarity_boost=0.5,
        output_file="output.mp3",
    ):
        try:
            data = {
                "text": text,
                "model_id": model_id,
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                },
            }

            response = requests.post(self.url, json=data, headers=self.headers)
            if response.status_code == 200:
                with open(output_file, "wb") as f:
                    for chunk in response.iter_content(chunk_size=self.chunk_size):
                        if chunk:
                            f.write(chunk)
                print(f"Audio saved to {output_file}")
            else:
                print(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"An error occurred during text-to-speech: {e}")
