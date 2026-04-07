# Use the official Python 3.10-slim image as the base
FROM python:3.10-slim

# Set the working directory within the container to /app
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the necessary dependencies specified in requirements.txt
# --no-cache-dir is used to keep the image size small
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the project files from the current directory into the container
COPY . .

# Expose port 10000 to allow network traffic to the container
EXPOSE 10000

# Command to start the FastAPI server using uvicorn
# Binds to 0.0.0.0 and listens on port 10000
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "10000"]
