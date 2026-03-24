# ---------------------------------------------------------------------------
# OCI Provider credentials
# ---------------------------------------------------------------------------
variable "tenancy_ocid" {
  description = "OCID del tenancy OCI"
  type        = string
}

variable "user_ocid" {
  description = "OCID del usuario OCI para autenticación con API Key"
  type        = string
}

variable "fingerprint" {
  description = "Fingerprint de la API Key del usuario OCI"
  type        = string
}

variable "private_key_path" {
  description = "Ruta local a la clave privada PEM de la API Key"
  type        = string
  default     = "~/.oci/oci_api_key.pem"
}

variable "region" {
  description = "Región OCI donde se desplegarán los recursos (e.g. us-chicago-1)"
  type        = string
}

# ---------------------------------------------------------------------------
# Compartment
# ---------------------------------------------------------------------------
variable "compartment_ocid" {
  description = "OCID del compartment donde se crearán los recursos"
  type        = string
}

# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------
variable "subnet_id" {
  description = "OCID de la subnet (pública o privada con Service Gateway) para Functions y API Gateway"
  type        = string
}

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------
variable "function_app_name" {
  description = "Nombre de la Functions Application"
  type        = string
  default     = "agente-ia-app"
}

variable "function_name" {
  description = "Nombre de la Function"
  type        = string
  default     = "agente-ia"
}

variable "function_image" {
  description = "Imagen Docker de la Function en OCIR (e.g. <region>.ocir.io/<namespace>/<repo>:<tag>)"
  type        = string
}

# ---------------------------------------------------------------------------
# API Gateway
# ---------------------------------------------------------------------------
variable "api_gateway_name" {
  description = "Nombre del API Gateway"
  type        = string
  default     = "agente-ia-gateway"
}

# ---------------------------------------------------------------------------
# OCI Generative AI
# ---------------------------------------------------------------------------
variable "genai_model_id" {
  description = "OCID del modelo de OCI Generative AI a usar"
  type        = string
}

variable "max_tokens" {
  description = "Número máximo de tokens en la respuesta del modelo"
  type        = number
  default     = 1024
}

variable "temperature" {
  description = "Temperatura del modelo (0.0 - 1.0)"
  type        = number
  default     = 0.7
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
variable "log_level" {
  description = "Nivel de log para la Function (DEBUG, INFO, WARNING, ERROR)"
  type        = string
  default     = "INFO"
}
