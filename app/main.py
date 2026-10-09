# Load built-in os module, allowing script to interact directly with the operating system, including reading environment variables.
import os

# Import flask framework
from flask import Flask

# Create the Application
app = Flask(__name__)

# Route an HTTP GET request to the root URL ("/") and return a JSON response
@app.get("/")
def index():
    return {"service": "sre-reliability-lab", "version": "0.1.0"}

# Route an HTTP GET request to the "/healthz" URL and return a JSON response indicating the health status of the service
# Kubernetes/Docker ecosystem uses this naming convention for health checks, so we will use it here as well.
@app.get("/healthz")
def healthz():
    return {"status": "healthy"}

# Route an HTTP GET request to the "/readyz" URL and return a JSON response indicating the readiness status of the service.
# The "true" value inside getenv() is the default value if the environment variable "APP_READY" is not set. If the value of "APP_READY" is "true", the service is considered ready and returns a 200 status code. Otherwise, it returns a 503 status code indicating that the service is not ready.
@app.get("/readyz")
def readyz():
    if os.getenv("APP_READY", "true") == "true":
        return {"status": "ready"}, 200
    else:
        return {"status": "not ready"}, 503
    