output "api_gateway_endpoint" {
  description = "Endpoint HTTPS público del API Gateway"
  value       = "https://${oci_apigateway_gateway.api_gw.hostname}/v1"
}

output "api_gateway_id" {
  description = "OCID del API Gateway"
  value       = oci_apigateway_gateway.api_gw.id
}

output "api_deployment_id" {
  description = "OCID del API Gateway Deployment"
  value       = oci_apigateway_deployment.api_deployment.id
}

output "function_app_id" {
  description = "OCID de la Functions Application"
  value       = oci_functions_application.fn_app.id
}

output "function_id" {
  description = "OCID de la Function"
  value       = oci_functions_function.agent_fn.id
}

output "log_group_id" {
  description = "OCID del Log Group"
  value       = oci_logging_log_group.fn_log_group.id
}

output "invoke_log_id" {
  description = "OCID del Log de invocaciones"
  value       = oci_logging_log.fn_invoke_log.id
}

output "dynamic_group_name" {
  description = "Nombre del Dynamic Group creado para las Functions"
  value       = oci_identity_dynamic_group.fn_dynamic_group.name
}

output "agent_endpoint" {
  description = "URL del endpoint del agente (POST)"
  value       = "https://${oci_apigateway_gateway.api_gw.hostname}/v1/agent"
}

output "health_endpoint" {
  description = "URL del endpoint de health check (GET)"
  value       = "https://${oci_apigateway_gateway.api_gw.hostname}/v1/health"
}
