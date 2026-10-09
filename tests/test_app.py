# Import the Flask application instance from the main module of the app package
from app.main import app

# Remove APP_READY so the application uses the fallback defined in main.py.
# Verify that an unset APP_READY produces HTTP 200 and {"status": "ready"}, based on behavior defined in main.py.
# monkeypatch is a pytest fixture that allows you to modify the behavior of objects for testing purposes. In this case, it is used to set the APP_READY environment variable to "true" for the duration of the test.
# raising=false is used to prevent an error from being raised if the environment variable does not exist.
def test_ready_by_default(monkeypatch):
    monkeypatch.delenv("APP_READY", raising=False)
    client = app.test_client()

    response = client.get("/readyz")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ready"}

# Test the /readyz endpoint when the APP_READY environment variable is set to "false"
def test_ready_if_false(monkeypatch):
    monkeypatch.setenv("APP_READY", "false")
    client = app.test_client()

    response = client.get("/readyz")

    assert response.status_code == 503
    assert response.get_json() == {"status": "not ready"}

# Test the /healthz endpoint when the APP_READY environment variable is set to "false"
# Verify the application remains healthy when configured as not ready.
def test_healthz(monkeypatch):
    monkeypatch.setenv("APP_READY", "false")
    client = app.test_client()

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.get_json() == {"status": "healthy"}