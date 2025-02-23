# Use the official Python 3.12 image from the Docker Hub
FROM python:3.10.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt from the root directory (same level as docker-compose.yml)
COPY ../requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code from the frontend directory
COPY frontend/ .

# Expose the port that Streamlit will run on
EXPOSE 8501

# Command to run the Streamlit app using the virtual environment's binary
CMD ["venv/bin/streamlit", "run", "streamlit_app.py"]
