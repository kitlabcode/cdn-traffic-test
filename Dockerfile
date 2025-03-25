# Use a recent Python Alpine image
FROM python:3.11-alpine

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for CrateDB and Python packages
RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev cargo

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the PYTHONPATH environment variable
ENV PYTHONPATH=/app

# Copy the application code into the container
COPY . /app/

# Expose the port for CrateDB (if needed for local testing)
EXPOSE 4200

# Set the default command to run pytest
CMD ["pytest", "-v", "-s", "tests/test_cdn_traffic.py"]