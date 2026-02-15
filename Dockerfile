FROM python:3.10-slim

# Install system dependencies required by PyMuPDF (fitz)
# libgl1-mesa-glx is often required for image processing in PDFs
# libglib2.0-0 is a common dependency for fitz
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create a non-root user to run the application (Production Best Practice)
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app

# Install Python dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser . .

# Switch to non-root user
USER appuser

# Run the bot application using the module name (executes bot/__main__.py)

CMD ["python", "-m", "bot"]
