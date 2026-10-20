FROM nvidia/cuda:11.7.1-base-ubuntu20.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y python3-pip python3-dev

# Copy application code
COPY . /app
WORKDIR /app

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose ports
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "octopus_brain.main:app", "--host", "0.0.0.0", "--port", "8000"]