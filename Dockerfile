# 1. Basimage
FROM python:3.11-slim

# 2. Skapa arbetskatalog
WORKDIR /app

# 3. Kopiera dependencies först
COPY requirements.txt .

# 4. Installera dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Kopiera resten av projektet
COPY . .

# 6. Exponera port
EXPOSE 5000

# 7. Kör Flask
CMD ["python", "app.py"]
