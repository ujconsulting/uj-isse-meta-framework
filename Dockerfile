FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data/output data/state

# Run as a normal user, not root.
#
# Everything above runs as root because installing packages needs it; everything
# below is the application, which needs nothing of the sort. It launches
# subprocesses and writes files under paths that come, in part, from HTTP
# requests -- so the difference between "a bug lets it write the wrong file" and
# "a bug lets it write any file in the image" is this one instruction.
#
# Ownership is handed over after the copy so the application can still write into
# data/, which it does on every run.
RUN useradd --create-home --uid 10001 isee \
    && chown -R isee:isee /app
USER isee

# Expose port for Flask app
EXPOSE 5001

# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONPATH=/app
ENV PORT=5001

# gunicorn, not `python app.py`.
#
# app.py's __main__ starts Flask's development server, which its own startup
# banner tells you not to use in production -- single-threaded, no request
# limits, a debugger one config flag away. The image was built for production
# (nixpacks.toml already serves this application with gunicorn) and ran it
# anyway.
#
# --workers 1 is deliberate and must stay 1, for the reason set out at length in
# nixpacks.toml: a run's status lives in a plain dict in one worker's memory, so
# a second worker answers "not found" for runs that are alive. Two copies of that
# reasoning would drift; the long version is there.
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5001} --workers 1 --timeout 300 --access-logfile - --error-logfile - app:app"]
