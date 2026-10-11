# Prometheus Application Monitoring Lab

## Application instrumentation

Installed prometheus-client and added a metrics handler at `/metrics`.

A Counter named `lab_http_requests_total` records responses using labels:

- method: HTTP method
- route: matched Flask route pattern
- status: HTTP response code

Flask's after_request hook increments the counter. The `/metrics`
endpoint exposes its current values; it does not perform the counting.

Unknown routes return HTTP 404 and are recorded with route="unmatched".
This is a metric label, not the response body. Grouping unknown paths
avoids a separate series for every arbitrary URL.

### Startup error

Initially encountered:

```text
NameError: name 'DispatcherMiddleware' is not defined
```

The middleware import must exist before the code uses it. This was an
application loading error, before the server began listening.

## Image and worker configuration

Updated the application's reported version to 0.2.0, built image
`sre-reliability-lab:0.2.0`, loaded it into kind, and updated the Deployment.

The version returned by `/` is application text. The Docker image tag is
a separate identifier; we manually kept them consistent.

Changed Gunicorn from two workers to one worker per container.

Python counters live in process memory. Multiple Gunicorn workers would
have independent counters unless multiprocess collection was configured.
For this lab, each Pod has one worker and one set of counters.

Two Kubernetes Pods still provide two application replicas.

Existing pytest tests passed, and the new image rolled out successfully.

## Prometheus configuration and discovery

Created a ConfigMap containing prometheus.yml.

The ConfigMap stores text in Kubernetes. Mounting it into the Prometheus
container makes that text available as a configuration file.

Configured Prometheus to:

- Scrape every 15 seconds.
- Discover Pods in the default namespace through the Kubernetes API.
- Keep running Pods labeled app=lab-api on declared port 8000.
- Request `/metrics` from each target.
- Attach the Pod name as a `pod` label.

Running Pods are retained even when unready so their diagnostic metrics
can still be collected.

Scraping individual Pods keeps their independent counters separate.
Scraping through a load-balancing Service could alternate between Pods
and misrepresent their counters as one series.

## Discovery permissions

Created a ServiceAccount, Role, and RoleBinding.

Granted get, list, and watch permissions for Pods in the default namespace.

Verified with kubectl auth can-i:

- list pods: yes
- delete pods: no

Reading Kubernetes metadata discovers target addresses. Scraping metrics
is a separate HTTP request to each application Pod.

## Prometheus deployment

Deployed the prebuilt Docker Hub image:

```text
prom/prometheus:v3.13.4
```

Mounted the configuration at `/etc/prometheus/prometheus.yml`.
Used emptyDir storage at `/prometheus` with 24-hour retention.

emptyDir survives container restarts within the Pod, but its history is
lost when the Pod is removed. Retention does not provide persistence.

Opened the interface using:

```bash
kubectl port-forward deployment/prometheus 9090:9090
```

Both application targets showed UP. UP means the metrics scrape succeeded;
it does not prove every application endpoint is healthy.

## Querying stored samples

```promql
lab_http_requests_total{job="lab-api"}
```

Returned separate samples for each Pod and route.

Application labels were method, route, and status.
Prometheus added job, instance, and our configured pod label.

This query reads stored samples rather than contacting the application
directly.

## Counters versus rates

A counter is a cumulative total since its process started.

```promql
rate(lab_http_requests_total{job="lab-api",route="/readyz"}[5m])
```

Calculated the average increase per second for each series over five
minutes. Each Pod showed approximately 0.2 requests/second.

```promql
sum(rate(lab_http_requests_total{job="lab-api",route="/readyz"}[5m]))
```

Combined both Pods' rates, giving approximately 0.4 requests/second.

Calculate rate before summing so counter resets are handled separately.

### Timing clarification

I initially mixed up the probe interval and scrape interval.

| Timing | Purpose |
|---|---|
| 5 seconds | Readiness probe interval per Pod |
| 15 seconds | Prometheus scrape interval |
| 5 minutes | History window used by the rate query |

Three Pods receiving one probe each every five seconds would produce
a total rate of 0.6 requests/second.

## User traffic experiment

Excluded probe routes:

```promql
sum(rate(lab_http_requests_total{
  job="lab-api",
  route!~"/healthz|/readyz"
}[5m]))
```

Generated 30 requests, approximately one per second:

```bash
for i in {1..30}; do
  curl -fsS http://localhost:8003/ > /dev/null
  sleep 1
done
```

Observed approximately 0.105 requests/second in the five-minute average.

The short burst ran near one request/second, but the query averaged it
across a much longer window.

The result displayed `{}` because sum combined all labels into one total.