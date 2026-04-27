
import base64
import io
import os
import tempfile
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const
from gtts import gTTS
import pyttsx3
from rembg import remove
from PIL import Image

# Kendi modülün
from astrology_calculator import generate_birth_chart_report

app = FastAPI(title="Astrology & Tool API")

# 🔹 CORS Ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔹 Dil Haritası
LANGUAGE_CODE_MAP = {
    "EN": "en", "FR": "fr", "DE": "de", "ES": "es",
    "IT": "it", "PT": "pt", "RU": "ru", "KO": "ko", "TR": "tr",
}

# --- Pydantic Modelleri (Data Validation) ---
class AscendantRequest(BaseModel):
    date: str
    time: str
    latitude: float
    longitude: float
    offset: str

class BirthChartRequest(BaseModel):
    date: str
    time: str
    latitude: float
    longitude: float
    offset: int

class TTSRequest(BaseModel):
    text: str
    lang: Optional[str] = "EN"

# --- Yardımcı Fonksiyonlar ---
def decimal_to_dms(decimal: float):
    deg = int(decimal)
    min_val = abs(decimal - deg) * 60
    return f"{deg}:{int(min_val)}"

# --- Endpointler ---

@app.post("/ascendant")
async def calculate_ascendant(data: AscendantRequest):
    try:
        lat_dms = decimal_to_dms(data.latitude)
        lon_dms = decimal_to_dms(data.longitude)
        location = GeoPos(lat_dms, lon_dms)
        dt = Datetime(data.date, data.time, data.offset)
        chart = Chart(dt, location)
        asc = chart.get(const.ASC)

        return {
            "ascendantSign": asc.sign,
            "ascendantSignDegree": asc.lon
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/birth_chart_report")
async def get_birth_chart_report_endpoint(data: BirthChartRequest):
    try:
        report = generate_birth_chart_report(
            data.date, data.time, data.latitude, data.longitude, data.offset
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/text_to_speech")
async def text_to_speech(data: TTSRequest):
    lang_code = LANGUAGE_CODE_MAP.get(data.lang.upper(), "en")
    try:
        tts = gTTS(text=data.text, lang=lang_code)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)

        audio_base64 = base64.b64encode(buf.read()).decode("utf-8")
        return {"audioContent": audio_base64}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/text_to_speech_offline")
async def text_to_speech_offline(data: TTSRequest):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
            tmp_path = tmpfile.name

        engine = pyttsx3.init()
        lang_code = LANGUAGE_CODE_MAP.get(data.lang.upper(), "en")
        voices = engine.getProperty("voices")
        
        selected = next((v.id for v in voices if lang_code in str(v.languages).lower()), None)
        if selected:
            engine.setProperty("voice", selected)

        engine.save_to_file(data.text, tmp_path)
        engine.runAndWait()

        with open(tmp_path, "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode("utf-8")

        os.remove(tmp_path)
        return {"audioContent": audio_base64}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/remove-bg")
async def remove_background(image: UploadFile = File(...)):
    try:
        # FastAPI'de UploadFile stream olarak gelir
        input_data = await image.read()
        input_image = Image.open(io.BytesIO(input_data))

        # Arka planı kaldır
        output_image = remove(input_image)

        # Çıktıyı belleğe al
        buffer = io.BytesIO()
        output_image.save(buffer, format="PNG")
        buffer.seek(0)

        img_base64 = base64.b64encode(buffer.read()).decode("utf-8")

        return {
            "status": "success",
            "image_base64": img_base64
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("APP_PORT", 7102))
    uvicorn.run(app, host="0.0.0.0", port=port)
