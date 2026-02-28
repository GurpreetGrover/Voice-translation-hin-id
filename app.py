# My code code below is recording the audio of user in one language and translating it in the other, for Hindi-Indonesian translation:

# ```

import os
from dotenv import load_dotenv
from mistralai import Mistral
import sounddevice as sd
import scipy.io.wavfile as wav
import time

# Load environment variables from .env file
load_dotenv()
api_key = os.getenv("MISTRAL_API_KEY")
cartesia_api_key = os.getenv("CARTESIA_API_KEY")

# Initialize the client (This was missing in your original snippet)
client = Mistral(api_key=api_key)


transcriptor = "voxtral-mini-latest"

translator = "ministral-14b-latest"


def record_audio_local(filename="recorded_audio.wav", duration=5, fs=44100):
    print(f"Recording for {duration} seconds...")
    # Record audio
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()  # Wait until recording is finished
    wav.write(filename, fs, recording)  # Save as WAV file
    print("Recording saved.")
    return filename

audio_file = record_audio_local()

start_time = time.perf_counter()

with open(audio_file, "rb") as f:


    transcription_response = client.audio.transcriptions.complete(

        model=transcriptor,

        file={

            "file_name": audio_file,

            "content": f.read(),  # Read the file as bytes

        }

    )

end_time = time.perf_counter()

print('\nTranscription latency- ', f"{(end_time-start_time):.3f}")

print("\n--- Transcription ---")

print(transcription_response.text)

start_time = time.perf_counter()

translation_response = client.chat.complete(

    model=translator,

    messages=[

        {

            "role": "system",

            "content":"""

            - You are a expert Hindi-Indonesian translator

            - User will send the input in Hindi or Indonesian, respond with the translation in other language

            - just respond with translation

            """

        },

        {
            "role": "user",
            "content": transcription_response.text,
        },

    ],

)

end_time = time.perf_counter()

print('\nTranslation latency- ', f"{(end_time-start_time):.3f}")

print("\n--- Translation ---")

print(translation_response.choices[0].message.content)

speak_these_words = translation_response.choices[0].message.content

#### Cartesia

import asyncio
from cartesia import AsyncCartesia

cartesia_client = AsyncCartesia(api_key=cartesia_api_key)

async def main():

    print("Generating audio...")
    start_time = time.perf_counter()  # Start the stopwatch
    
    # Await the new .generate() method to get the complete audio payload
    audio_response = await cartesia_client.tts.generate(
        model_id="sonic-3",
        transcript=speak_these_words,
        voice={
            "mode": "id",
            "id": "6ccbfb76-1fc6-48f7-b71d-91ac6298247b",
        },
        language="id",
        output_format={
            "container": "wav",
            "sample_rate": 44100,
            "encoding": "pcm_s16le",
        },
    )
    # Use Cartesia's built-in file saver instead of f.write()
    await audio_response.write_to_file("sonic-3.wav")
    end_time = time.perf_counter()  # Stop the stopwatch
    latency = end_time - start_time
    print(f"Total TTS Generation Time: {latency:.3f} seconds")


if __name__ == "__main__":
    asyncio.run(main())

# Read the audio file
fs, data = wav.read("sonic-3.wav")

print("Playing translation...")
# Play the audio natively through Python
sd.play(data, fs)
sd.wait()  # Wait for the playback to finish before continuing
print("response_ended")