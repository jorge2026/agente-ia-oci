# Cost Management

## Cost drivers

This solution can incur costs in several OCI services. Actual charges depend on region, model, request volume, token usage, gateway configuration, logging volume, and current OCI pricing.

| Cost area | Main driver | Cost-control approach |
|---|---|---|
| OCI Generative AI | Model, input/output tokens, request volume | Set token limits, select fit-for-purpose models, track usage |
| OCI Functions | Invocations, execution duration, allocated memory | Avoid unnecessary calls, monitor duration, right-size memory |
| API Gateway | Gateway/deployment usage and traffic | Monitor request volume and avoid unused deployments |
| OCI Logging | Ingestion, retention, and query volume | Use appropriate retention and avoid verbose sensitive logs |
| Networking | Data transfer and network architecture | Review egress and private connectivity design |

## Controls already present

- `MAX_PROMPT_CHARS` limits prompt size.
- `MAX_TOKENS_LIMIT` caps the requested output token count.
- `MAX_TOKENS` and `TEMPERATURE` provide defaults.
- Function memory and timeout are explicitly configured in Terraform and the Fn manifest.

These controls help bound individual requests but do not establish an overall monthly spend limit.

## Recommended financial controls

- Configure OCI budgets and cost alerts at the appropriate compartment or tenancy scope.
- Set model/service quotas and application-level per-consumer request limits.
- Track request counts and token consumption by environment and application.
- Establish a maximum monthly spend and an owner for exception approval.
- Review logs retention and API Gateway/network architecture for unnecessary cost.
- Use separate development and production compartments.
- Revisit model selection based on quality, latency, and total cost per successful task.

## Cost estimation worksheet

Before deployment, collect:

- Expected requests per day and month.
- Average input tokens per request.
- Average output tokens per request.
- Selected model and region.
- Average Function execution duration and memory.
- Expected log ingestion and retention.
- Gateway and network traffic assumptions.

Use the official OCI pricing and the selected model's regional pricing to calculate estimates. Do not treat sample values or estimates as a quote.
