import swisseph as swe
import datetime

# Efemeris dosya yolu
# Swisseph efemeris dosyalarını bu dizine yerleştirmelisiniz.
# Örneğin: 'ephe' klasörünü projenizin kök dizinine koyun.
swe.set_ephe_path('./ephe')

zodiac_signs_english = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Gezegen yorumları (sade)
planet_comments = {
    'Sun': "Kimliğin, yaşam enerjin.",
    'Moon': "Duygusal dünyan, tepkilerin.",
    'Mercury': "Zihin ve iletişim tarzın.",
    'Venus': "Aşk, estetik ve değer yargıların.",
    'Mars': "Mücadele, enerji ve tutkun.",
    'Jupiter': "Şans, gelişim ve genişleme alanların.",
    'Saturn': "Sorumluluk, disiplin ve hayat derslerin.",
    'Uranus': "Farklılık ve ani değişimlerin.",
    'Neptune': "Hayal gücü, ilham ve sezgilerin.",
    'Pluto': "Dönüşüm, güç ve kriz yönetimin.",
    'True Node': "Karmik yolun, ruhsal yönelimin."
}

# Dereceye göre burç adını döndürür
def get_zodiac(degree):
    index = int(degree // 30)
    return zodiac_signs_english[index]

# Doğum haritası raporu oluşturan ana fonksiyon
def generate_birth_chart_report(birth_date_str, birth_time_str, latitude, longitude, utc_offset):
    """
    Verilen doğum bilgileriyle bir doğum haritası raporu oluşturur.

    Args:
        birth_date_str (str): Doğum tarihi 'YYYY-MM-DD' formatında.
        birth_time_str (str): Doğum saati 'HH:MM' formatında.
        latitude (float): Doğum yerinin enlemi (decimal).
        longitude (float): Doğum yerinin boylamı (decimal).
        utc_offset (int): UTC ofseti (örn: +3 için 3, -5 için -5).

    Returns:
        dict: Gezegen konumları ve yorumlarını içeren bir sözlük.
    """
    # Tarih ve saat stringlerini datetime objelerine dönüştür
    birth_date = datetime.datetime.strptime(birth_date_str, '%Y-%m-%d').date()
    birth_time = datetime.datetime.strptime(birth_time_str, '%H:%M').time()

    # UTC zamanına çevir
    dt = datetime.datetime.combine(birth_date, birth_time)
    dt_utc = dt - datetime.timedelta(hours=utc_offset)

    # Julian günü hesapla
    jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                    dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600)

    # Hesaplamak istediğimiz gezegenler ve onlara karşılık gelen swisseph ID'leri
    planets = {
        'Sun': swe.SUN,
        'Moon': swe.MOON,
        'Mercury': swe.MERCURY,
        'Venus': swe.VENUS,
        'Mars': swe.MARS,
        'Jupiter': swe.JUPITER,
        'Saturn': swe.SATURN,
        'Uranus': swe.URANUS,
        'Neptune': swe.NEPTUNE,
        'Pluto': swe.PLUTO,
        'True Node': swe.TRUE_NODE # Kuzey Ay Düğümü
    }

    report_data = {
        "birthDateUTC": dt_utc.strftime('%Y-%m-%d %H:%M:%S'),
        "coordinates": {"latitude": latitude, "longitude": longitude},
        "planetPositions": []
    }

    for name, pid in planets.items():
        # Gezegenin ekliptik boylamını hesapla
        # swe.calc_ut: UTC zamanına göre gezegenin konumunu hesaplar
        # swe.FLG_SWIEPH: Swisseph'in kendi efemeris dosyalarını kullanmasını sağlar
        pos, _ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH)
        
        # Gezegenin derecesini 0-360 aralığına getir
        degree = pos[0] % 360
        
        # Burcu ve yorumu al
        sign = get_zodiac(degree)
        comment = planet_comments.get(name, "Yorum bulunamadı.")
        
        # Rapor verisine ekle
        report_data["planetPositions"].append({
            "planet": name,
            "degree": round(degree, 2),
            "sign": sign,
            "comment": comment
        })

    return report_data