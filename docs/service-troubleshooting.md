# Kubernetes Service Selector Troubleshooting

## Scenario

Application Pods were Running and Ready, but the Service had no backends
because its selector did not match their labels.

## Controlled fault

Changed the live Service selector:

```bash
kubectl patch service lab-api --type=merge \
  -p '{"spec":{"selector":{"app":"lab-api-mismatch"}}}'
```

This changed the live object only. The committed Service YAML remained
correct, and the application Pods were unchanged.

## Investigation

Compared the Service selector with Pod labels:

```bash
kubectl get service lab-api \
  -o jsonpath='{.spec.selector}{"\n"}'

kubectl get pods --show-labels
```

Observed:

- Service selector: app=lab-api-mismatch
- Application Pod labels: app=lab-api
- Both application Pods remained Running and Ready.

Inspected the Service:

```bash
kubectl describe service lab-api
```

The Service still had its ClusterIP and port mapping, but its Endpoints
field was empty.

## Root cause

A Service selects Pods by matching labels. The incorrect selector
matched neither application Pod, leaving no backends for Service traffic.

Healthy Pods alone do not guarantee working Service routing.

## Recovery

Reapplied the correct configuration:

```bash
kubectl apply -f k8s/service.yaml
```

Verified through the actual Service from inside the cluster:

```bash
kubectl exec deployment/lab-api -- python -c 'import urllib.request; r = urllib.request.urlopen("http://lab-api/", timeout=5); print(r.status); print(r.read().decode())'
```

Result:

```text
200
{"service":"sre-reliability-lab","version":"0.2.0"}
```

## Lessons

- Check Service selectors, Pod labels, and endpoints when ready Pods
  cannot be reached through a Service.
- A Service can exist with a valid IP and port but no matching backends.
- Restarting healthy application Pods would not correct this selector.
- Reapplying correct YAML can restore a manually changed live object.
- In this lab, Prometheus discovers Pods directly, so successful metrics
  scrapes would not prove the application Service works.

  ## Liveness probe misconfiguration

Created a separate test Pod named lab-api-liveness, labeled
app=lab-api-liveness so the application Service would not select it.

Set APP_READY=true and retained the readiness check on /readyz.
Deliberately configured the liveness probe to request /does-not-exist.

### Evidence

- Pod was Running and Ready.
- Liveness requests returned HTTP 404.
- Restart Count increased.
- Events explicitly reported that the failed liveness probe caused
  Kubernetes to restart the container.
- The previous container exited with code 0: a graceful shutdown
  can still result from Kubernetes terminating it.

The container restarted within the same Pod; Kubernetes did not create
a replacement Pod.

### Important distinction

The probe configuration determines Kubernetes' action, not the URL name.

- Repeated readiness failures exclude the Pod from normal Service traffic.
- Repeated liveness failures cause the container to restart.

Using /readyz as a liveness check could cause unnecessary restarts during
temporary unreadiness.

### Recovery

Deleted the test Pod, corrected its liveness path to /healthz,
and recreated it.

Verified Ready 1/1 and zero restarts after approximately one minute.
Deleted the test Pod after verification.