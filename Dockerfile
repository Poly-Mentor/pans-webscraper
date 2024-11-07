FROM python:3.12-alpine

COPY requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install --no-cache-dir -r requirements.txt

COPY app.py /app

CMD ["python3", "-u", "app.py"]