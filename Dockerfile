# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file first for better caching
COPY src/requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the source code into the container
COPY src/ .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using uvicorn from the virtual environment
CMD ["venv/bin/uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]