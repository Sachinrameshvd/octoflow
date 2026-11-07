FROM nvidia/cuda:11.7.1-base-ubuntu20.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y python3-pip python3-dev build-essential libssl-dev libffi-dev libxml2-dev libxmlsec1-dev zlib1g-dev

# Install Python packages
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set working directory
WORKDIR /app

# Expose ports
EXPOSE 5000

# Command to run the application
CMD ["python3", "app.py"]