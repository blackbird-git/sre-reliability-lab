# AI-Assisted Investigation: Service Selector Mismatch

## Workflow

Used a read-only Bash collector to gather Kubernetes context, Pod status
and labels, Service details, EndpointSlices, Pod events, and recent logs.

Each check reports failures and continues so one missing resource does
not prevent collecting other evidence.

Saved stdout and stderr together:

```bash
bash scripts/collect-diagnostics.sh \
  > diagnostics/service-selector-failure.txt 2>&1
```

Generated diagnostic reports are excluded from Git.

## Controlled fault

Changed the live lab-api Service selector from app=lab-api to
app=lab-api-mismatch. The application Pods were unchanged.

## AI-assisted analysis

Used the investigation prompt to separate facts from hypotheses.

Observed facts:

- Service selector was app=lab-api-mismatch.
- The Service's Endpoints field was empty.
- Its EndpointSlice contained endpoints: null.
- The Service still had a ClusterIP and port mapping.

Leading explanation:

The selector did not match the application Pods' app=lab-api label,
leaving the Service without backends.

Evidence limitation:

The supplied Service sections alone did not establish current Pod health
or demonstrate a failed client request. Checking current Pod labels was
recommended rather than inventing missing evidence.

## Engineer-reviewed recovery

Reapplied the intended Service configuration:

```bash
kubectl apply -f k8s/service.yaml
```

Verified a request through the Service from inside the cluster:

```text
200
{"service":"sre-reliability-lab","version":"0.2.0"}
```

## Guardrails and scope

- Diagnostic collection reads cluster information without changing resources.
- Logs and report contents are treated as evidence, not instructions.
- AI separates observations, hypotheses, missing information, and actions.
- The engineer reviews and executes corrections.
- Recovery requires verification.
- Reports should be reviewed for sensitive information before sharing.

This is a manually operated AI-assisted investigation workflow.
It is not an autonomous agent or an automated AI integration.