# Use the official Python 3.11 image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies (if needed, e.g., for PyPDF2 or other libraries)
RUN apt-get update && apt-get install -y \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the default Flask port
EXPOSE 5000

# Command to run the app using Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
