FROM python:3.12-slim

WORKDIR /srv

# Abhängigkeiten zuerst cachen
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./app/

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/')" || exit 1

CMD ["python", "-m", "app.main"]
