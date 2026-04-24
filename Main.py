
from flask import Flask, request, jsonify
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import const
from astrology_calculator import generate_birth_chart_report
from gtts import gTTS
import pyttsx3
import base64
import io
import tempfile
import os
from flask_cors import CORS
from rembg import remove
from PIL import Image


app = Flask(__name__)

CORS(app)  # 🔹 Tüm domainlerden erişime izin verir


# 🔹 Enum Language map
LANGUAGE_CODE_MAP = {
    "EN": "en",  # English
    "FR": "fr",  # French
    "DE": "de",  # German
    "ES": "es",  # Spanish
    "IT": "it",  # Italian
    "PT": "pt",  # Portuguese
    "RU": "ru",  # Russian
    "KO": "ko",  # Korean
    "TR": "tr",  # Turkish
}

def decimal_to_dms(decimal):
    deg = int(decimal)
    min = abs(decimal - deg) * 60
    return f"{deg}:{int(min)}"

@app.route('/ascendant', methods=['POST'])
def calculate_ascendant():
    data = request.get_json()
    date = data.get('date')
    time_str = data.get('time')
    latitude = float(data.get('latitude'))
    longitude = float(data.get('longitude'))
    offset = data.get('offset')

    lat_dms = decimal_to_dms(latitude)
    lon_dms = decimal_to_dms(longitude)
    location = GeoPos(lat_dms, lon_dms)
    dt = Datetime(date, time_str, offset)
    chart = Chart(dt, location)
    asc = chart.get(const.ASC)

    return jsonify({
        "ascendantSign": asc.sign,
        "ascendantSignDegree": asc.lon
    })

@app.route('/birth_chart_report', methods=['POST'])
def get_birth_chart_report():
    data = request.get_json()
    required_params = ['date', 'time', 'latitude', 'longitude', 'offset']
    for param in required_params:
        if param not in data:
            return jsonify({"error": f"Missing parameter: {param}"}), 400

    birth_date = data.get('date')
    birth_time = data.get('time')
    latitude = float(data.get('latitude'))
    longitude = float(data.get('longitude'))
    utc_offset = int(data.get('offset'))

    try:
        report = generate_birth_chart_report(birth_date, birth_time, latitude, longitude, utc_offset)
        return jsonify(report)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🔹 Online TTS (gTTS)
@app.route('/text_to_speech', methods=['POST'])
def text_to_speech():
    data = request.get_json()
    text = data.get("text")
    lang_enum = data.get("lang", "EN")  # default English

    if not text:
        return jsonify({"error": "Missing text parameter"}), 400

    lang_code = LANGUAGE_CODE_MAP.get(lang_enum.upper(), "en")

    try:
        tts = gTTS(text=text, lang=lang_code)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)

        audio_base64 = base64.b64encode(buf.read()).decode("utf-8")
        return jsonify({"audioContent": audio_base64})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🔹 Offline TTS (pyttsx3)
@app.route('/text_to_speech_offline', methods=['POST'])
def text_to_speech_offline():
    data = request.get_json()
    text = data.get("text")
    lang_enum = data.get("lang", "EN")

    if not text:
        return jsonify({"error": "Missing text parameter"}), 400

    try:
        # Geçici dosyaya yaz
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
            tmp_path = tmpfile.name

        engine = pyttsx3.init()

        # 🔹 uygun dili destekleyen sesi seçmeye çalış
        lang_code = LANGUAGE_CODE_MAP.get(lang_enum.upper(), "en")
        voices = engine.getProperty("voices")
        selected = None
        for v in voices:
            if lang_code in str(v.languages).lower():
                selected = v.id
                break
        if selected:
            engine.setProperty("voice", selected)

        engine.save_to_file(text, tmp_path)
        engine.runAndWait()

        with open(tmp_path, "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode("utf-8")

        os.remove(tmp_path)
        return jsonify({"audioContent": audio_base64})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/remove-bg", methods=["POST"])
def remove_background():
    # Resim dosyasını istekte kontrol et
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files["image"]

    try:
        # Resmi oku
        input_image = Image.open(image_file.stream)

        # Arka planı kaldır
        output_image = remove(input_image)

        # Çıktıyı bellek tamponuna al
        buffer = io.BytesIO()
        output_image.save(buffer, format="PNG")
        buffer.seek(0)

        # Base64'e çevir
        img_base64 = base64.b64encode(buffer.read()).decode("utf-8")

        # JSON olarak döndür
        return jsonify({
            "status": "success",
            "image_base64": img_base64
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv("APP_PORT", 7102))
    app.run(host='0.0.0.0', port=port, debug=True)
