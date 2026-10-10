# Python Service Lab

## Build the Docker image

```bash
docker build -t sre-reliability-lab:0.1.0 .
```

## Start the application container

```bash
docker run -d --name lab-api -p 127.0.0.1:8000:8000 sre-reliability-lab:0.1.0
```

## Start a container with readiness disabled

```bash
docker run -d --name lab-api-unready -p 127.0.0.1:8001:8000 -e APP_READY=false sre-reliability-lab:0.1.0
```

## Readiness behavior

With `APP_READY` unset, `/readyz` uses the default `"true"` from
`main.py` and returns HTTP 200 with `{"status":"ready"}`.

With `APP_READY=false`, `/readyz` returns HTTP 503 with
`{"status":"not ready"}`.

The `/healthz` endpoint returns HTTP 200 in both cases.

## RUN versus CMD

`RUN` executes commands during the image build.
`CMD` defines the default command executed when a container starts.

## Network binding

The application listens on `0.0.0.0` inside the container so it can
accept traffic forwarded to the container's network interface.

Publishing the host port on `127.0.0.1` limits access to the local host.

