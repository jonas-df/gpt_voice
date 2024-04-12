#!/usr/bin/env python3
import asyncio
import edge_tts


class EdgeTTS:
    def __init__(self, text: str, voice: str = "en-GB-SoniaNeural"):
        self.text = text
        self.voice = voice

    async def save_to_file(self, output_file: str) -> None:
        communicate = edge_tts.Communicate(self.text, self.voice)
        await communicate.save(output_file)

    @staticmethod
    def run(text: str, voice: str, output_file: str):
        tts_instance = EdgeTTS(text, voice)

        loop = asyncio.get_event_loop_policy().get_event_loop()
        try:
            loop.run_until_complete(tts_instance.save_to_file(output_file))
        finally:
            loop.close()


# Usage example
if __name__ == "__main__":
    EdgeTTS.run("Hello World!", "en-GB-SoniaNeural", "output.mp3")
