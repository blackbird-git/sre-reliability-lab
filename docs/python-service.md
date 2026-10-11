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



## Troubleshooting: running container, unreachable application

### Goal

Demonstrate that a running container does not guarantee the application
is reachable through its published port.

### Reproduce the failure

Start a container with Gunicorn listening only on the container's loopback
address:

```bash
docker run -d --name lab-api-loopback \
  -p 127.0.0.1:8002:8000 \
  sre-reliability-lab:0.1.0 \
  gunicorn --bind 127.0.0.1:8000 --workers 2 --access-logfile - app.main:app
```

The command after the image name overrides the Dockerfile's default CMD.

```bash
docker ps
docker logs lab-api-loopback
curl -i --max-time 5 http://localhost:8002/healthz
```

Observed results:

- Docker reported the container as Up.
- Gunicorn logged that it was listening on 127.0.0.1:8000.
- The host request failed with "Connection reset by peer".
- No HTTP status code was received. This differs from an HTTP 503,
  which is a response returned by the application.

### Root cause

Inside a container, 127.0.0.1 refers to that container's loopback interface.
Gunicorn bound to this address accepts connections through loopback only.

Docker forwards published-port traffic to the container's network
interface. Gunicorn therefore needs to listen on that interface,
or on 0.0.0.0, which includes all IPv4 interfaces in the container.

### Mistake: changing the host address instead of the application address

I initially changed the port mapping to:

```
-p 0.0.0.0:8002:8000
```

However, Gunicorn still used:

```
--bind 127.0.0.1:8000
```

This expanded the host-side publishing address but did not change the
application's listener inside the container. The request still failed.

These settings have separate purposes:

- `-p 127.0.0.1:8002:8000`: publish host port 8002 on localhost and
  forward traffic to container port 8000.
- `--bind 0.0.0.0:8000`: make Gunicorn accept traffic on all IPv4
  interfaces inside the container.

### Fix and verification

Recreate the test container with the corrected application bind address:

```bash
docker rm -f lab-api-loopback

docker run -d --name lab-api-loopback \
  -p 127.0.0.1:8002:8000 \
  sre-reliability-lab:0.1.0 \
  gunicorn --bind 0.0.0.0:8000 --workers 2 --access-logfile - app.main:app
```

Verify from the host:

```bash
curl -i --max-time 5 http://localhost:8002/healthz
```

The request returned HTTP 200 and:

```json
{"status":"healthy"}
```

No image rebuild was needed because only the container's startup command
changed.

### Additional command lessons

- `docker run -d` starts the container in detached mode and returns
  control to the terminal.
- The image name is `sre-reliability-lab:0.1.0`. Misspelling it as
  `ste-reliability-lab:0.1.0` caused Docker to attempt a registry pull
  because it could not find that image locally.


### Operational takeaway

Check process status, listening address, port mapping, and an actual
request. Container status and successful startup logs alone do not
prove that users can reach the application.