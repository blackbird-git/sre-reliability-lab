# Kubernetes Deployment, Service, and Readiness Lab

## Goal

Run the containerized Python service in Kubernetes, observe Pod replacement,
and verify how readiness affects Service routing.

## Local cluster

Created a kind cluster named `sre-lab` using Kubernetes v1.36.4.

- kind runs the Kubernetes node as a Docker container.
- kubectl communicates with the Kubernetes API.
- The active kubectl context is `kind-sre-lab`.
- The single node runs both control-plane components and application workloads.
- Two application replicas on one node do not provide protection against
  that node failing.

Loaded the application image into the node:

```bash
kind load docker-image sre-reliability-lab:0.1.0 --name sre-lab
```

The node has its own container runtime and image storage. An image available
to host Docker is not automatically available inside the node.

## Deployment and desired state

Applied `k8s/deployment.yaml`, requesting two Pods, each containing one
application container:

```bash
kubectl apply -f k8s/deployment.yaml
kubectl rollout status deployment/lab-api --timeout=90s
kubectl get pods -o wide
```

Deleting one managed Pod caused a replacement Pod to be created with a new
name. This was a new Pod, rather than a container restart in the surviving Pod.

### How reconciliation works

Kubernetes does not repeatedly read the local YAML file.

`kubectl apply` sends the desired configuration to the Kubernetes API.
Controllers watch cluster objects and reconcile actual state with stored
desired state.

- The Deployment manages ReplicaSets and rollouts.
- The ReplicaSet maintains the requested number of Pods.
- The kubelet runs assigned Pods' containers on the node.

Editing local YAML alone does not update the cluster; it must be applied.

Terraform also uses desired state, but normally reconciles when an apply
runs. Kubernetes controllers reconcile continuously.

## Service networking

Applied `k8s/service.yaml`:

```bash
kubectl apply -f k8s/service.yaml
```

The Service is named `lab-api`. `ClusterIP` is its type, not its name.

It provides a stable internal IP and DNS name and selects Pods labeled
`app: lab-api`. Normal Service traffic reaches eligible matching Pods.

| Setting | Purpose |
|---|---|
| Service port 80 | Port clients use to reach the Service |
| targetPort 8000 | Application listening port in the Pods |
| Local port 8003 | Temporary host access through port-forward |

### Port-forward correction

```bash
kubectl port-forward service/lab-api 8003:80
```

I initially described local traffic as using port 80. The local client
actually connects to `localhost:8003`.

Port-forward resolves Service port 80 to targetPort 8000 and forwards
directly to a selected backing Pod. It does not send requests through
the Service's cluster IP or demonstrate Service load balancing.

## Readiness and liveness probes

Added HTTP probes to the Deployment's Pod template:

- Readiness: `/readyz`, port 8000, every 5 seconds.
- Liveness: `/healthz`, port 8000, every 10 seconds.

The kubelet checks each Pod directly.

Repeated readiness failures exclude a Pod from normal Service traffic.
Repeated liveness failures cause its container to restart.

Before probes were configured, `READY 1/1` did not mean Kubernetes had
checked `/readyz`.

Applying the updated Pod template triggered a rollout. Both replacement
Pods became ready.

## Unready test Pod

Applied a standalone test Pod from `k8s/unready-pod.yaml` with:

- The same `app: lab-api` label used by the Service.
- `APP_READY=false`.
- Readiness and liveness probes.

```bash
kubectl apply -f k8s/unready-pod.yaml
kubectl describe pod lab-api-unready
kubectl get endpointslices \
  -l kubernetes.io/service-name=lab-api -o yaml
```

Observed:

- The test Pod remained Running.
- Its Ready condition was False.
- Readiness probe events reported HTTP 503.
- Its restart count remained zero.
- Its EndpointSlice entry had `ready: false`.
- Both Deployment Pods had `ready: true`.

The Service selects by labels, rather than by whether a Pod belongs to a
particular Deployment.

## Service request versus direct Pod request

From a healthy Pod, requested:

```text
http://lab-api/readyz
```

Result:

```text
200
{"status":"ready"}
```

This used Service DNS and Service port 80 to reach an eligible Pod.

Then requested the unready Pod directly at its observed IP:

```text
http://10.244.0.10:8000/readyz
```

Result:

```text
503
{"status":"not ready"}
```

Pod IPs can change; this address records the specific lab observation.

## Operational takeaway

Running, ready, and reachable describe different conditions.

Readiness controls eligibility for normal Service traffic. It does not
block direct requests to a Pod, and a readiness failure does not itself
restart the container.