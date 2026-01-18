# Use lightweight Python image (Alpine)
FROM python:3.12-alpine

# Set working directory
WORKDIR /app

# Install build dependencies for compiling any Python packages
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    libffi-dev \
    && apk add --no-cache bash

# Copy dependency file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Remove build dependencies to keep image small
RUN apk del .build-deps

# Copy application code
COPY . .

# Expose the port used in docker-compose.yml
EXPOSE 8000

# Run the application via Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "run:app"]

