# Prometheus Readiness Alert Lab

## Goal

Define an alert, trigger it with a controlled readiness failure, and
observe its state transitions.

## Rule

Created a ConfigMap named prometheus-alerts containing alerts.yml.

The LabReadinessFailures rule evaluates:

```promql
sum by (pod) (
  rate(lab_http_requests_total{
    job="lab-api",
    route="/readyz",
    status="503"
  }[1m])
) > 0
```

Configured:

- Evaluation interval: 15 seconds.
- Query history window: 1 minute.
- Pending period (`for`): 1 minute.
- Severity label: warning.
- Summary identifying the Pod.

The history window calculates the recent failure rate. The pending period
requires the condition to remain active before the alert fires.

## Loading the rule

Mounted the rule ConfigMap at:

```text
/etc/prometheus/rules
```

Added this to prometheus.yml:

```yaml
rule_files:
  - /etc/prometheus/rules/alerts.yml
```

The mount supplies the file; rule_files tells Prometheus to read it.

Applying the Deployment changes replaced the Prometheus Pod.
Its emptyDir metrics history was lost, but configuration was reloaded.

Verified that LabReadinessFailures appeared on the Prometheus Alerts page.

## Controlled failure

Applied k8s/unready-pod.yaml, using image 0.2.0 and APP_READY=false.

Prometheus scraped all three matching application Pods. The alert queried
their stored metrics, selecting only /readyz responses with status 503.

The application returned 503 because APP_READY was false.
The Kubernetes readiness probe generated the requests; it did not
determine their response codes.

The two healthy Pods continued returning 200 and did not match the rule.

Because the expression retains the pod label, the alert identified
lab-api-unready separately.

## Observed lifecycle

1. Inactive: the condition was not active.
2. Pending: a positive readiness-failure rate was detected.
3. Firing: the condition persisted for the configured minute.
4. Inactive: after removing the test Pod, the expression stopped matching.

Cleaned up:

```bash
kubectl delete -f k8s/unready-pod.yaml
```

Removing the target resolved this alert condition. It did not prove that
the failed application recovered.

## Operational limits

This rule detects readiness failure responses, not user-facing outages.

It does not detect an application that cannot respond or expose metrics.
Missing data is not equivalent to a healthy result.

The healthy Deployment Pods remained available throughout the experiment.

Prometheus evaluated the alert, but no external notification was configured.
Alertmanager would provide notification routing, grouping, and silencing.