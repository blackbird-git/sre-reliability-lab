# Grafana Dashboard and Readiness Experiment

## Goal

Connect Grafana to Prometheus, visualize request rates, and distinguish
successful metrics collection from application readiness.

## Prometheus Service and DNS

Created a ClusterIP Service named `prometheus`, exposing port 9090
and forwarding to Prometheus's port 9090.

Verified access from an application Pod:

```bash
kubectl exec deployment/lab-api -- python -c 'import urllib.request; r = urllib.request.urlopen("http://prometheus:9090/-/ready"); print(r.status); print(r.read().decode())'
```

Result: HTTP 200, "Prometheus Server is Ready."

### Networking clarification

The Service provides a stable internal address for Grafana to use.
It does not expose Prometheus to the host browser.

| Client | Address | Access method |
|---|---|---|
| Host browser | localhost:9090 | Temporary port-forward |
| Grafana Pod | prometheus:9090 | Cluster DNS and Service networking |

Kubernetes DNS resolves `prometheus` to the Service's ClusterIP.

The name comes from the Service's metadata.name, not from deploying
Grafana. Both resources are in the default namespace, so Grafana can
use the short name.

The full Service name in this cluster is:

```text
prometheus.default.svc.cluster.local
```

Service networking routes connections to the matching Prometheus Pod.
The Pod can be replaced without changing the Service address.

## Grafana deployment and data source

Deployed Grafana using:

```text
grafana/grafana:12.4.0
```

Used emptyDir storage mounted at `/var/lib/grafana`.

Opened the interface through:

```bash
kubectl port-forward deployment/grafana 3000:3000
```

Configured a Prometheus data source with:

- URL: http://prometheus:9090
- Scrape interval setting: 15s

Save & test succeeded.

Grafana's backend queries Prometheus from inside the cluster.
Using localhost:9090 would refer to Grafana's own Pod.

Grafana queries stored metrics; it does not scrape our application.

## Dashboard panels

### Application request rate

Visualization: Time series. Unit: requests/sec.

```promql
sum(rate(lab_http_requests_total{
  job="lab-api",
  route!~"/healthz|/readyz"
}[5m]))
```

Excludes Kubernetes probe routes and combines application request rates.

The earlier traffic burst appeared in the graph. The plotted values
represent a five-minute average, rather than the instantaneous burst rate.

### Metrics targets UP

Visualization: Stat. Calculation: Last (not null). Unit: None.

```promql
sum(up{job="lab-api"})
```

Initially displayed 2.

Prometheus generates up for each target:

- 1: latest metrics scrape succeeded.
- 0: latest metrics scrape failed.

This does not prove application readiness or successful user requests.
A target removed from discovery eventually disappears from current query
results, so this panel does not establish the intended replica count.

### Readiness probe response rate by status

Visualization: Time series. Unit: requests/sec.

```promql
sum by (status) (
  rate(lab_http_requests_total{
    job="lab-api",
    route="/readyz"
  }[5m])
)
```

Set the query's custom legend to:

```text
HTTP {{status}}
```

This substitutes each series' status label, producing names such as
HTTP 200 and HTTP 503.

The query legend setting names the series. The panel legend options
control how those names are displayed.

## Unready Pod experiment

Updated k8s/unready-pod.yaml to use image 0.2.0.
Retained APP_READY=false, the app=lab-api label, and both probes.

```bash
kubectl apply -f k8s/unready-pod.yaml
```

Observed:

- HTTP 200 readiness responses remained near 0.4 requests/sec.
- A new HTTP 503 response-rate series appeared.
- Metrics targets UP increased from 2 to 3.
- The test Pod's Service endpoint had ready=false.

The HTTP 503 line measured response rate, not the number of failed Pods.
Its initial values varied while samples accumulated. Readiness probes
may also run more frequently while a Pod is unready.

### Conclusion

The unready Pod remained observable through Prometheus while Kubernetes
excluded it from normal Service traffic.

Metrics scrape success, application readiness, and user-facing
availability are different signals.

## Cleanup and dashboard export

Removed the standalone test Pod:

```bash
kubectl delete -f k8s/unready-pod.yaml
```

Saved the dashboard as SRE Reliability Lab and exported its JSON to:

```text
dashboards/sre-reliability-lab.json
```

The export preserves dashboard definitions and queries. It does not
contain metrics history or the Prometheus data-source configuration.

Grafana's emptyDir data is lost if its Pod is removed, so the export
provides a recoverable dashboard definition.

## Reproducible Grafana provisioning

### Problem

Grafana used emptyDir storage, so replacing its Pod removed its database,
including manually configured data sources and dashboards.

We moved the required configuration into files stored in Git and
Kubernetes ConfigMaps.

### Data-source provisioning

Created `k8s/grafana-datasource.yaml` with:

- Prometheus URL: http://prometheus:9090
- Data-source UID: ag0xg0rcsy9dsb
- Expected scrape interval: 15s
- UI editing disabled

Reused the UID referenced by the exported dashboard so its panels could
find the recreated data source.

Mounted the ConfigMap at:

```text
/etc/grafana/provisioning/datasources
```

Grafana reads these provisioning files during startup.

The interval setting informs Grafana's queries; it does not change
Prometheus's scrape schedule.

### Troubleshooting: the Deployment had not changed

Initially, the browser still showed the old dashboards.

Inspection showed:

- The Grafana Pod was still 26 hours old.
- The Deployment remained at revision 1.
- The new configuration mount was absent from the live Deployment.

`kubectl rollout status` reported success for the existing configuration.
It did not prove that the intended local edits had been applied.

Saved and applied the updated Deployment. A new Pod appeared, and its
fresh database contained no dashboards.

Verified that the Prometheus data source existed automatically, then
successfully imported the exported dashboard.

### Dashboard provisioning

Generated a ConfigMap manifest from the dashboard JSON:

```bash
kubectl create configmap grafana-dashboard \
  --from-file=sre-reliability-lab.json=dashboards/sre-reliability-lab.json \
  --dry-run=client -o yaml > k8s/grafana-dashboard.yaml
```

`--dry-run=client` generates the object locally. It does not create it
in Kubernetes. The shell redirect saves the YAML to a file.

Applied that manifest and a dashboard-provider ConfigMap.

The provider tells Grafana to load JSON from:

```text
/var/lib/grafana/dashboards
```

It places the dashboard in the Labs folder, checks files every 10 seconds,
and disables saving UI changes.

Mounted:

| Configuration | Container directory |
|---|---|
| Data-source instructions | /etc/grafana/provisioning/datasources |
| Dashboard-provider instructions | /etc/grafana/provisioning/dashboards |
| Dashboard JSON | /var/lib/grafana/dashboards |

### Verification

Reviewed the Deployment changes before applying:

```bash
kubectl diff -f k8s/grafana-deployment.yaml
```

Applied the Deployment and waited for its rollout.

After reconnecting the port-forward, the replacement Grafana Pod
automatically contained:

- The Prometheus data source.
- The SRE Reliability Lab dashboard in the Labs folder.
- Working dashboard panels.

No manual data-source creation or dashboard import was required.

### Limits and source of truth

This recreates configuration; it does not preserve Grafana's database,
changed passwords, or Prometheus metric history.

The dashboard JSON is the editable source. The generated ConfigMap
manifest contains a copy and must be regenerated when that JSON changes.
ConfigMap changes alone do not trigger a Deployment rollout.