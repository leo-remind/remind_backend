import io
import logging
import os

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import Response
from pydub import AudioSegment

load_dotenv()
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)

app = FastAPI()

SARVAM_URL = "https://api.sarvam.ai/speech-to-text-translate"
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")


@app.post("/concatenate-wav/")
async def concatenate_wavs(
    files: list[UploadFile] = File(..., description="WAV files to concatenate"),
):
    try:
        audio_segments = []
        c = 0
        for file in files:
            file_bytes = await file.read()
            audio = AudioSegment.from_wav(io.BytesIO(file_bytes))
            # 16kHz sample rate, 16-bit depth, 1 channel.
            audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            audio.export(f"file{c}.wav", format="wav")
            audio_segments.append(audio)
            print("NEw add")
            c+=1

        combined_audio = sum(audio_segments[1:], audio_segments[0])
        
        combined_audio.export("file.wav", format="wav")

        buffer = io.BytesIO()
        combined_audio.export(buffer, format="wav")
        buffer.seek(0)

        payload = {"model": "saaras:v2", "with_diarization": "true"}
        files = [("file", ("combined.wav", buffer, "audio/wav"))]
        headers = {"api-subscription-key": SARVAM_API_KEY}

        resp = requests.request(
            "POST", SARVAM_URL, headers=headers, data=payload, files=files
        )
        logger.debug(resp.json())
        # print(resp.json())
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers),
        )

    except Exception as e:
        return {"error": f"Audio processing failed: {str(e)}"}
