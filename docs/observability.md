# Observability and Operations

## Current signals

The current implementation writes application log messages to standard error and provisions OCI Logging resources for Function invocation logs.

The Function currently emits basic events for:

- Request method and route.
- Mock mode activation.
- Model invocation metadata (session ID, temperature, and token limit).
- Successful response generation.
- Provider invocation failures.

Do not log prompt text, credentials, authorization headers, or personal data.

## Recommended telemetry model

| Signal | Suggested measurements | Purpose |
|---|---|---|
| Traffic | Request count by route and status | Understand usage |
| Latency | End-to-end latency and model-call latency, p50/p95/p99 | Detect slow responses |
| Errors | 4xx, 5xx, provider errors, throttles | Detect failures |
| Model usage | Input/output tokens where available, model identifier | Understand consumption |
| Function | Invocation count, duration, memory, throttles | Capacity and reliability |
| Gateway | Access and execution logs | Diagnose routing and gateway behavior |

## Recommended dashboards

1. **Service health:** request rate, availability, error rate, latency.
2. **Model operations:** model calls, throttling, token usage, provider errors.
3. **Cost and capacity:** estimated model spend, Function invocations, duration, and configured quotas.

The dashboards and alerts above are recommendations; they are not provisioned by the current Terraform configuration.

## Suggested alerts

Set thresholds with the service owner and actual baseline data. Examples:

- Sustained increase in 5xx responses.
- Model provider throttling or authentication failures.
- p95 latency above the agreed service objective.
- Function throttling or repeated timeouts.
- Unexpected growth in request or token consumption.

## Operational runbook

### Health check

```bash
curl --fail --silent --show-error "$API_BASE/v1/health"
```

### Invoke the agent

```bash
curl --fail --silent --show-error \
  -X POST "$API_BASE/v1/agent" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Explain cloud architecture in one paragraph.","max_tokens":256}'
```

### Troubleshooting sequence

1. Confirm API Gateway deployment and route configuration.
2. Check Function invocation status and logs.
3. Verify Function configuration values (region, compartment, model ID).
4. Verify Resource Principal permissions for OCI Generative AI.
5. Confirm model availability and service quotas in the target region.
6. Review timeout and payload limits before increasing capacity.

## Service objectives

Define service-level indicators and objectives only after collecting representative workload data. Do not publish availability or latency guarantees based solely on this reference implementation.
