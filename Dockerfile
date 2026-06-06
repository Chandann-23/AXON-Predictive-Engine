# Use the official Python 3.10-slim image as the base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend files to the container
COPY backend/ .

# Expose port 7860 (Hugging Face Spaces requirement)
EXPOSE 7860

# Run the FastAPI application using uvicorn
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "7860"]
