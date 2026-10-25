FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create directory for database
RUN mkdir -p /app/data

# Expose port for web app
EXPOSE 8000

# Run both bot and web app
CMD ["python", "main.py"]
