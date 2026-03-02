# My code code below is recording the audio of user in one language and translating it in the other, for Hindi-Indonesian translation:

import os
import time
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Response
from mistralai import Mistral
from cartesia import AsyncCartesia
import urllib.parse
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
api_key = os.getenv("MISTRAL_API_KEY")
cartesia_api_key = os.getenv("CARTESIA_API_KEY")

# Initialize clients and FastAPI app
mistral_client = Mistral(api_key=api_key)
cartesia_client = AsyncCartesia(api_key=cartesia_api_key)
app = FastAPI()

# Allow your frontend to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace "*" with your frontend's actual URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-STT-Latency", "X-Translation-Latency", "X-TTS-Latency", "X-Transcribed-Text", "X-Translated-Text"] # You MUST expose custom headers so JavaScript can read them
)

transcriptor = "voxtral-mini-latest"
translator = "ministral-14b-latest"

@app.post("/translate-audio")
async def translate_audio_endpoint(audio: UploadFile = File(...)):
    # 1. Read the uploaded audio file from the frontend
    audio_bytes = await audio.read()
    
    # --- STT: Transcription ---
    stt_start = time.perf_counter()
    transcription_response = mistral_client.audio.transcriptions.complete(
        model=transcriptor,
        file={
            "file_name": audio.filename,
            "content": audio_bytes,
        }
    )
    stt_latency = time.perf_counter() - stt_start
    transcribed_text = transcription_response.text

    # --- Translation ---
    trans_start = time.perf_counter()
    translation_response = mistral_client.chat.complete(
        model=translator,
        messages=[
            {
                "role": "system",
                "content":"""
                You are a strict, expert bilingual translator for Hindi and Indonesian. 
            
                CRITICAL RULES:
                1. If the input is in Hindi (including Romanized Hindi/Hinglish), you MUST output Indonesian. Prefix it with "id|".
                2. If the input is in Indonesian, you MUST output Hindi. Prefix it with "hi|".
                3. NEVER translate into English.
                4. Example 1: id|Ini adalah terjemahan.
                5. Example 2: hi|यह एक अनुवाद है।
                6. Output ONLY the prefix and the raw translated text. No introductions, no explanations, no quotes.
                """
            },
            {"role": "user", "content": transcribed_text},
        ],
    )

    trans_latency = time.perf_counter() - trans_start
    raw_output = translation_response.choices[0].message.content

    # Split the language tag from the text (with a fallback just in case)
    if "|" in raw_output:
        target_lang, translated_text = raw_output.split("|", 1)
        target_lang = target_lang.strip().lower()
        translated_text = translated_text.strip()
    else:
        target_lang = "id" # Fallback
        translated_text = raw_output.strip()

    # Map the detected language to the correct Cartesia voice ID
    voice_map = {
        "id": "b441c4fd-4910-4c55-ae56-f0291057e2cc",
        "hi": "791d5162-d5eb-40f0-8189-f19db44611d8" 
    }
    selected_voice_id = voice_map.get(target_lang, "6ccbfb76-1fc6-48f7-b71d-91ac6298247b")

    # --- TTS: Generation ---
    tts_start = time.perf_counter()
    audio_response = await cartesia_client.tts.generate(
        model_id="sonic-3",
        transcript=translated_text,
        voice={
            "mode": "id",
            "id": selected_voice_id,
        },
        language=target_lang, # Pass the dynamic language variable here
        output_format={
            "container": "wav",
            "sample_rate": 44100,
            "encoding": "pcm_s16le",
        },
    )
    
    # trans_latency = time.perf_counter() - trans_start
    # translated_text = translation_response.choices[0].message.content

    # # --- TTS: Generation ---
    # tts_start = time.perf_counter()
    # audio_response = await cartesia_client.tts.generate(
    #     model_id="sonic-3",
    #     transcript=translated_text,
    #     voice={
    #         "mode": "id", # identitifier
    #         "id": "6ccbfb76-1fc6-48f7-b71d-91ac6298247b",
    #     },
    #     language="id",
    #     output_format={
    #         "container": "wav",
    #         "sample_rate": 44100,
    #         "encoding": "pcm_s16le",
    #     },
    # )
    
    # Save temporarily to send back
    output_filename = "temp_output.wav"
    await audio_response.write_to_file(output_filename)
    tts_latency = time.perf_counter() - tts_start

    # Read the generated file to send it over HTTP
    with open(output_filename, "rb") as f:
        final_audio_bytes = f.read()

    # --- Return Response ---
    # We use custom headers to send the latency tracking metadata back to the frontend
    headers = {
        "X-STT-Latency": f"{stt_latency:.3f}",
        "X-Translation-Latency": f"{trans_latency:.3f}",
        "X-TTS-Latency": f"{tts_latency:.3f}",
        "X-Transcribed-Text": urllib.parse.quote(transcribed_text), 
        "X-Translated-Text": urllib.parse.quote(translated_text)
    }

    return Response(content=final_audio_bytes, media_type="audio/wav", headers=headers)
    
# print('\nTranscription latency- ', f"{(end_time-start_time):.3f}")

# print("\n--- Transcription ---")

# print(transcription_response.text)

# start_time = time.perf_counter()

# translation_response = mistral_client.chat.complete(

#     model=translator,
#     messages=[
#         {
#             "role": "system",
#             "content":"""
#             - You are a expert Hindi-Indonesian translator
#             - User will send the input in Hindi or Indonesian, respond with the translation in other language
#             - just respond with translation
#             """
#         },
#         {
#             "role": "user",
#             "content": transcription_response.text,
#         },

#     ],

# )

# end_time = time.perf_counter()

# print('\nTranslation latency- ', f"{(end_time-start_time):.3f}")

# print("\n--- Translation ---")

# print(translation_response.choices[0].message.content)

# speak_these_words = translation_response.choices[0].message.content

# #### Cartesia

# import asyncio
# from cartesia import AsyncCartesia

# cartesia_client = AsyncCartesia(api_key=cartesia_api_key)

# async def main():

#     print("Generating audio...")
#     start_time = time.perf_counter()  # Start the stopwatch
    
#     # Await the new .generate() method to get the complete audio payload
#     audio_response = await cartesia_client.tts.generate(
#         model_id="sonic-3",
#         transcript=speak_these_words,
#         voice={
#             "mode": "id",
#             "id": "6ccbfb76-1fc6-48f7-b71d-91ac6298247b",
#         },
#         language="id",
#         output_format={
#             "container": "wav",
#             "sample_rate": 44100,
#             "encoding": "pcm_s16le",
#         },
#     )
#     # Use Cartesia's built-in file saver instead of f.write()
#     await audio_response.write_to_file("sonic-3.wav")
#     end_time = time.perf_counter()  # Stop the stopwatch
#     latency = end_time - start_time
#     print(f"Total TTS Generation Time: {latency:.3f} seconds")


# if __name__ == "__main__":
#     asyncio.run(main())

# # Read the audio file
# fs, data = wav.read("sonic-3.wav")

# print("Playing translation...")
# # Play the audio natively through Python
# sd.play(data, fs)
# sd.wait()  # Wait for the playback to finish before continuing
# print("response_ended")