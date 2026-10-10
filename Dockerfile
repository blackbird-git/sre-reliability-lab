# Start with an image that has Python installed. The "slim" variant is a smaller image that contains only the essential components needed to run Python, which helps reduce the size of the final Docker image.
FROM python:3.14-slim

# Set the working directory inside the container to /service. This is where the application code and dependencies will be placed.
WORKDIR /service

# Copy the requirements.txt file from the host machine to the working directory in the container. This file contains a list of Python packages that need to be installed for the application to run.
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy the application code from the host machine's app/ directory to the working directory in the container. This includes all the Python files and other resources needed for the application.
COPY app/ ./app/

# Create a non-root user named "appuser" to run the application. Running applications as a non-root user is a security best practice, as it limits the potential damage that can be done if the application is compromised.
RUN useradd --create-home appuser
USER appuser

# Expose port 8000 to allow external access to the application. This is the port that the application will listen on for incoming HTTP requests.
EXPOSE 8000

# Use Gunicorn as the WSGI HTTP server to serve the Flask application. The command specifies that Gunicorn should bind to all network interfaces on port 8000, use 2 worker processes to handle requests, and log access information to standard output. The application instance is specified as "app.main:app", which tells Gunicorn where to find the Flask application object.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "app.main:app"]