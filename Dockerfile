FROM python:3.13.2-slim

# install deps.
RUN apt-get update && apt-get install -y \
    ansible \
    awscli \
    bsdmainutils \
    iputils-ping \
    make \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# set workdir.
WORKDIR /app

# install project-specific deps.
COPY inventory/requirements.txt ./
RUN pip install --no-cache-dir -r inventory/requirements.txt

