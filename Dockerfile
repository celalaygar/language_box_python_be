FROM python:3.11-slim

# Sistem güncelle ve derleme araçlarını kur
RUN apt-get update && \
    apt-get install -y gcc build-essential pkg-config espeak-ng && \
    rm -rf /var/lib/apt/lists/*


# Çalışma dizini
WORKDIR /app

# Gereksinim dosyasını kopyala ve yükle
COPY requirements.txt .

# Gerekli bağımlılıkları yükle
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir onnxruntime  # 🔹 Burada eksik modül yükleniyor

# Uygulamayı kopyala
COPY . .

# Ortam değişkenlerini kullanmak için (isteğe bağlı)
ENV FLASK_ENV=production

# Flask varsayılan portu
EXPOSE 7102

# Başlat
CMD ["python", "main1.py"]

