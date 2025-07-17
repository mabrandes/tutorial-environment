# Use a minimal Python base image
FROM python:3.10-slim

# Environment variables to make Python behave nicely
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy requirements first
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the application code
COPY . /app

# Expose port 80, since your compose maps 8083:80
EXPOSE 80

# Command to run your Flask app
CMD ["python", "main_sign_in_up.py"]
