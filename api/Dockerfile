FROM python:3.9-slim

WORKDIR /app

# Copy requirements files
COPY api/requirements.txt /app/api-requirements.txt
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt
RUN pip install --no-cache-dir -r /app/api-requirements.txt

# Copy the project
COPY src/ /app/src/
COPY api/ /app/api/
COPY data/ /app/data/
COPY .env /app/.env

# Change to the API directory
WORKDIR /app/api

# Set environment variables
ENV PYTHONPATH=/app

# Expose the port
EXPOSE 8000

# Start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 