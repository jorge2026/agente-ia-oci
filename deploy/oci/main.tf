terraform {
  required_version = ">= 1.7.0"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0.0"
    }
  }
}

# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------
provider "oci" {
  region           = var.region
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
}

# ---------------------------------------------------------------------------
# Logging — Log Group para la Function
# ---------------------------------------------------------------------------
resource "oci_logging_log_group" "fn_log_group" {
  compartment_id = var.compartment_ocid
  display_name   = "${var.function_name}-log-group"
}

resource "oci_logging_log" "fn_invoke_log" {
  display_name = "${var.function_name}-invoke-log"
  log_group_id = oci_logging_log_group.fn_log_group.id
  log_type     = "SERVICE"

  configuration {
    source {
      category    = "invoke"
      resource    = oci_functions_application.fn_app.id
      service     = "functions"
      source_type = "OCISERVICE"
    }
    compartment_id = var.compartment_ocid
  }

  is_enabled = true
}

# ---------------------------------------------------------------------------
# IAM — Dynamic Group para las Functions
# ---------------------------------------------------------------------------
resource "oci_identity_dynamic_group" "fn_dynamic_group" {
  compartment_id = var.tenancy_ocid
  name           = "${var.function_name}-dg"
  description    = "Dynamic group for ${var.function_name} OCI Functions"
  matching_rule  = "ALL {resource.type = 'fnfunc', resource.compartment.id = '${var.compartment_ocid}'}"
}

# ---------------------------------------------------------------------------
# IAM — Policies
# ---------------------------------------------------------------------------
resource "oci_identity_policy" "fn_genai_policy" {
  compartment_id = var.compartment_ocid
  name           = "${var.function_name}-genai-policy"
  description    = "Allow Functions to call OCI Generative AI and write logs"

  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.fn_dynamic_group.name} to use generative-ai-family in compartment id ${var.compartment_ocid}",
    "Allow dynamic-group ${oci_identity_dynamic_group.fn_dynamic_group.name} to use log-content in compartment id ${var.compartment_ocid}",
  ]
}

resource "oci_identity_policy" "apigw_fn_policy" {
  compartment_id = var.compartment_ocid
  name           = "${var.function_name}-apigw-policy"
  description    = "Allow API Gateway to invoke Functions"

  statements = [
    "Allow any-user to use functions-family in compartment id ${var.compartment_ocid} where all {request.principal.type='ApiGateway', request.resource.compartment.id='${var.compartment_ocid}'}",
  ]
}

# ---------------------------------------------------------------------------
# Functions Application
# ---------------------------------------------------------------------------
resource "oci_functions_application" "fn_app" {
  compartment_id = var.compartment_ocid
  display_name   = var.function_app_name
  subnet_ids     = [var.subnet_id]

  config = {
    OCI_REGION     = var.region
    COMPARTMENT_ID = var.compartment_ocid
    GENAI_MODEL_ID = var.genai_model_id
    MAX_TOKENS     = tostring(var.max_tokens)
    TEMPERATURE    = tostring(var.temperature)
    LOG_LEVEL      = var.log_level
  }
}

# ---------------------------------------------------------------------------
# Function
# ---------------------------------------------------------------------------
resource "oci_functions_function" "agent_fn" {
  application_id     = oci_functions_application.fn_app.id
  display_name       = var.function_name
  image              = var.function_image
  memory_in_mbs      = "256"
  timeout_in_seconds = 120

  config = {}

  provisioned_concurrency_config {
    strategy = "NONE"
  }
}

# ---------------------------------------------------------------------------
# API Gateway
# ---------------------------------------------------------------------------
resource "oci_apigateway_gateway" "api_gw" {
  compartment_id = var.compartment_ocid
  display_name   = var.api_gateway_name
  endpoint_type  = "PUBLIC"
  subnet_id      = var.subnet_id
}

resource "oci_apigateway_deployment" "api_deployment" {
  compartment_id = var.compartment_ocid
  display_name   = "${var.api_gateway_name}-deployment"
  gateway_id     = oci_apigateway_gateway.api_gw.id
  path_prefix    = "/v1"

  specification {
    routes {
      path    = "/agent"
      methods = ["POST"]

      backend {
        type        = "ORACLE_FUNCTIONS_BACKEND"
        function_id = oci_functions_function.agent_fn.id
      }

      request_policies {
        header_transformations {
          set_headers {
            items {
              name      = "Content-Type"
              values    = ["application/json"]
              if_exists = "OVERWRITE"
            }
          }
        }
      }
    }

    routes {
      path    = "/health"
      methods = ["GET"]

      backend {
        type        = "ORACLE_FUNCTIONS_BACKEND"
        function_id = oci_functions_function.agent_fn.id
      }
    }

    logging_policies {
      access_log {
        is_enabled = true
      }
      execution_log {
        is_enabled = true
        log_level  = "INFO"
      }
    }
  }
}
