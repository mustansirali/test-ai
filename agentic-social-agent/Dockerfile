# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose default FastAPI port
EXPOSE 8080

# Start FastAPI app
CMD ["uvicorn", "serve:app", "--host", "0.0.0.0", "--port", "8080"]