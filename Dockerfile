# Use the official Python 3.12-slim as the base image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy requirements.txt into the container
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files into the container
COPY . /app/

# Expose the port (FastAPI uses 8000 by default)
EXPOSE 8000

# Startup command: run main:app using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
