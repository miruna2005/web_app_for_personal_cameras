FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn opencv-python-headless flask
COPY . .
EXPOSE 5000
RUN apt-get update && apt-get install -y ffmpeg libsm6 libxext6
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
RUN pip install --no-cache-dir -r requirements.txt