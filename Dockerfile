FROM python:3.8-slim
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y
WORKDIR /code
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD [ "python", "./gesturesensor.py" ]