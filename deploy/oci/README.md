# Terraform — deploy/oci/

Este directorio contiene la infraestructura como código (Terraform) para desplegar el **Agente de IA** en OCI.

## Recursos creados

| Recurso | Tipo | Descripción |
|---|---|---|
| `oci_functions_application` | Functions | Aplicación que contiene la Function |
| `oci_functions_function` | Functions | La Function del agente |
| `oci_apigateway_gateway` | API Gateway | Gateway HTTPS público |
| `oci_apigateway_deployment` | API Gateway | Rutas `/agent` y `/health` |
| `oci_identity_dynamic_group` | IAM | Dynamic Group para Functions |
| `oci_identity_policy` | IAM | Policies GenAI + Logging + API Gateway |
| `oci_logging_log_group` | Logging | Log Group para la Function |
| `oci_logging_log` | Logging | Log de invocaciones |

## Pasos previos requeridos (manuales)

> ⚠️ Terraform **no puede crear** un repositorio de contenedores (OCIR) ni hacer el build/push de la imagen Docker. Estos pasos son manuales:

1. **Crear repositorio en OCIR** (una vez):
   ```bash
   oci artifacts container repository create \
     --compartment-id $COMPARTMENT_ID \
     --display-name agente-ia-oci/agente-ia
   ```

2. **Build y push de la imagen** (cada deploy):
   ```bash
   cd ../../function/
   fn build
   # o con Docker directamente:
   docker build -t us-chicago-1.ocir.io/<namespace>/agente-ia-oci/agente-ia:1.0.0 .
   docker push us-chicago-1.ocir.io/<namespace>/agente-ia-oci/agente-ia:1.0.0
   ```

3. Una vez que tengas la imagen en OCIR, pon su URI completa en `function_image` de `terraform.tfvars`.

## Uso

```bash
# 1. Copiar y completar variables
cp terraform.tfvars.example terraform.tfvars
# Edita terraform.tfvars

# 2. Inicializar
terraform init

# 3. Ver plan
terraform plan

# 4. Aplicar
terraform apply

# 5. Ver outputs (endpoint público)
terraform output api_gateway_endpoint
```

## Outputs principales

| Output | Descripción |
|---|---|
| `api_gateway_endpoint` | Base URL del API Gateway |
| `agent_endpoint` | URL completa de POST /agent |
| `health_endpoint` | URL completa de GET /health |
| `function_id` | OCID de la Function |
| `log_group_id` | OCID del Log Group |
