# Use an official Python runtime as the parent image
FROM python:3.8-slim-buster

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg-dev \
    libz-dev \
    libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install the Python dependencies
COPY requirements.txt /app/
WORKDIR /app
RUN pip3 install --upgrade pip \
    && pip3 install -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY . /app/

# Specify the command to run on container start
CMD ["gunicorn", "TruckImageSearch.wsgi:application", "--bind", "0.0.0.0:8080"]
