# Security Design and Hardening

## Current security controls

The repository currently includes:

- OCI Resource Principal authentication from the Function to OCI services.
- OCI IAM Dynamic Group and policy resources managed by Terraform.
- Example environment files and Terraform variables are excluded from Git by `.gitignore`.
- Input validation for prompt length, temperature, and maximum output tokens.
- A configured prompt-size limit and token limit.

These controls are a starting point, not a complete production security boundary.

## Security gaps to address before production

| Area | Current state | Required action |
|---|---|---|
| API consumer identity | No end-user authentication in the Function/API design | Add JWT/OAuth2 or an approved identity integration |
| Authorization | No tenant- or user-level authorization | Define caller roles and resource access rules |
| Public exposure | Terraform creates a public API Gateway | Restrict ingress and evaluate WAF/private access |
| Abuse prevention | No per-consumer rate limiting shown | Add throttling, quotas, and request budgets |
| Error handling | Provider exception details may be returned to callers | Return generic client errors and log sanitized diagnostics |
| Prompt safety | Basic shape and length validation only | Add policy controls, prompt-injection testing, and output handling appropriate to the use case |
| Secrets | Runtime uses Resource Principals; local/CI credential examples exist | Use a secret manager for any credentials that are genuinely required; never commit real values |
| Supply chain | CI runs lint/smoke checks and Terraform validation | Add dependency pinning, vulnerability scanning, and image scanning |
| Data handling | No explicit retention/classification policy | Define data classification, retention, and logging redaction rules |

## IAM least-privilege review

Review every policy statement against the exact Function, compartment, and API Gateway deployment. Prefer the narrowest supported permissions and resource scopes. Avoid broad tenancy-level permissions where a compartment-level permission is sufficient.

The current Terraform policy allowing API Gateway to invoke Functions should be reviewed against OCI's current policy syntax and the intended gateway/deployment scope before production use.

## Secure operating practices

- Never commit `.env`, `terraform.tfvars`, private keys, API keys, OCIDs belonging to real production resources, or customer data.
- Rotate any credential that may have been exposed.
- Use separate compartments and identities for development, staging, and production.
- Keep request bodies and prompts out of application logs unless there is an approved data-handling reason.
- Avoid returning raw provider exceptions, stack traces, OCIDs, or internal configuration to API consumers.
- Establish a vulnerability-reporting and incident-response process.

## Security acceptance checklist

- [ ] API authentication and authorization are enabled.
- [ ] Public access is restricted or explicitly approved.
- [ ] IAM policies have been reviewed for least privilege.
- [ ] Rate limits and per-consumer quotas are configured.
- [ ] Logs exclude secrets and sensitive prompt content.
- [ ] Dependency and container image scanning are enabled.
- [ ] Data retention and incident response are documented.
- [ ] Security tests are part of CI/CD.
