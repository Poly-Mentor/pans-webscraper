FROM python:3.11-alpine

COPY requirements.txt /app/requirements.txt

WORKDIR /app

RUN apk add --no-cache gcc musl-dev python3-dev libffi-dev openssl-dev
RUN pip3 install --no-cache-dir -r requirements.txt

COPY app.py /app

CMD ["python3", "-u", "app.py"]