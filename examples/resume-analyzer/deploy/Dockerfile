FROM nvidia/cuda:11.7.1-base-ubuntu20.04

RUN apt-get update && apt-get install -y python3-pip

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]