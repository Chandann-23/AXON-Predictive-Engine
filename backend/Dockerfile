# Use the official Python 3.10-slim image as the base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend files
COPY . .

# Hugging Face Spaces requires port 7860
EXPOSE 7860

# Start the FastAPI server
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "7860"]
