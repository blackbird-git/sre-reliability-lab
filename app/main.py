# Load built-in os module, allowing script to interact directly with the operating system, including reading environment variables.
import os

# Import flask framework. Flask is a lightweight web framework for Python that allows you to build web applications quickly and easily.
from flask import Flask

# Import the make_wsgi_app function from the prometheus_client library, which is used to create a WSGI application for exposing Prometheus metrics.
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

# Import the Counter class from the prometheus_client library, which is used to create a counter metric for tracking the number of requests to the application.
from flask import Flask, request
from prometheus_client import Counter, make_wsgi_app

# Create the Application
app = Flask(__name__)

# Serve Prometheus metrics separately from the Flask application routes.
app.wsgi_app = DispatcherMiddleware(
    app.wsgi_app,
    {"/metrics": make_wsgi_app()},
)

# Create a Prometheus counter metric to track the total number of HTTP requests received by the application, labeled by method, route, and status code. 
HTTP_REQUESTS = Counter(
    "lab_http_requests_total",
    "Total HTTP responses by method, route, and status",
    ["method", "route", "status"],
)

@app.after_request
def record_request(response):
    route = request.url_rule.rule if request.url_rule else "unmatched"

    HTTP_REQUESTS.labels(
        method=request.method,
        route=route,
        status=str(response.status_code),
    ).inc()

    return response

# Route an HTTP GET request to the root URL ("/") and return a JSON response
@app.get("/")
def index():
    return {"service": "sre-reliability-lab", "version": "0.2.0"}

# Route an HTTP GET request to the "/healthz" URL and return a JSON response indicating the health status of the service
# Kubernetes/Docker ecosystem uses this naming convention for health checks, so we will use it here as well.
@app.get("/healthz")
def healthz():
    return {"status": "healthy"}

# Route an HTTP GET request to the "/readyz" URL and return a JSON response indicating the readiness status of the service.
# The "true" value inside getenv() is the default value if the environment variable "APP_READY" is not set. If the value of "APP_READY" is "true", the service is considered ready and returns a 200 status code. Otherwise, it returns a 503 status code indicating that the service is not ready.
@app.get("/readyz")
def readyz():
    if os.getenv("APP_READY", "false") == "true":
        return {"status": "ready"}, 200
    else:
        return {"status": "not ready"}, 503


    