# ADR 0001: Serverless OCI Reference Architecture

- **Status:** Accepted for this reference implementation
- **Date:** 2026-11-21

## Context

The project needs a small HTTP interface for experimenting with OCI Generative AI without operating a long-running application server. It should be reproducible and provisioned with Infrastructure as Code.

## Decision

Use OCI API Gateway as the HTTPS entry point, OCI Functions for request handling, OCI Generative AI for text generation, OCI IAM Resource Principals for Function-to-service authentication, and Terraform for infrastructure provisioning.

## Consequences

### Positive

- No application server fleet to patch or operate.
- Clear separation between API routing, request handling, and model inference.
- OCI Resource Principals avoid storing an OCI API private key in the Function runtime.
- Infrastructure can be reviewed and version-controlled.

### Trade-offs and limitations

- The request path is synchronous and inherits model latency.
- Function and gateway timeouts must be aligned with model response times.
- Public gateway exposure requires a deliberate authentication and abuse-protection design.
- The current implementation does not provide conversation memory, end-user identity, or tenant isolation.

## Follow-up decisions

- Define API authentication and authorization.
- Define operational SLOs from measured workloads.
- Evaluate asynchronous processing if inference latency or client timeouts require it.
- Define multi-environment state and deployment promotion.
