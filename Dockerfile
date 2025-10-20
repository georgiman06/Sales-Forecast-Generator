# Use official lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Prophet / PyStan
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libatlas-base-dev \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy files to container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir \
    Flask==3.0.2 \
    prophet==1.1.4 \
    pystan==2.19.1.1 \
    plotly==5.22.0 \
    pandas==2.2.2 \
    numpy==1.23.5 \
    scikit-learn==1.3.2 \
    gunicorn==21.2.0 \
    cmdstanpy==1.1.0 \
    Cython==0.29.36

# Expose the default port
EXPOSE 10000

# Start the app
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]
