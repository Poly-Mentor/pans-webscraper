FROM python:3.12-alpine

COPY requirements.txt /

RUN pip3 install --no-cache-dir -r requirements.txt

COPY app.py /

COPY settings.yaml /

CMD ["python3", "-u", "app.py"]