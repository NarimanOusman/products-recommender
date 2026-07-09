FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy all project files at once
# This is much cleaner and avoids filename mismatches!
COPY . /app/

# Install dependencies
# Update this line in your Dockerfile
RUN pip install --no-cache-dir fastapi uvicorn pydantic numpy scikit-learn joblib requests
# Expose port
EXPOSE 8000

# Start the app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
# Update your RUN line to this:
