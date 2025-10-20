FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1

# System dependencies for Prophet / Numpy
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libatlas-base-dev \
    liblapack-dev \
    gfortran \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip wheel setuptools
RUN pip install pystan==2.19.1.1 prophet==1.1.5 --no-cache-dir
RUN pip install -r requirements.txt --no-cache-dir

EXPOSE 5000
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
