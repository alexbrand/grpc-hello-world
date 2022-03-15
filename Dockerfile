FROM python:3.9-slim

RUN apt update && apt install -y gcc

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .
COPY client.py .
COPY helloworld.proto .

CMD ["python", "server.py"]
