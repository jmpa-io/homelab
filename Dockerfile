FROM python:3.13.2-slim

# Install deps.
RUN apt-get update && apt-get install -y \
    ansible \
    awscli \
    bsdmainutils \
    iputils-ping \
    make \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set workdir.
WORKDIR /app

# Install project-specific deps.
COPY inventory/requirements.txt ./
RUN pip install --no-cache-dir -r ./requirements.txt

