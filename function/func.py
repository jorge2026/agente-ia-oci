"""
OCI Function — Agente de IA
Recibe peticiones JSON con 'prompt' y llama a OCI Generative AI.
"""

import io
import json
import logging
import os
import sys

import fdk.response

# ---------------------------------------------------------------------------
# Logging estructurado
# ---------------------------------------------------------------------------
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    stream=sys.stderr,
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

SERVICE_NAME = "agente-ia-oci"
VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Helper: respuesta JSON estándar
# ---------------------------------------------------------------------------
def _json_response(ctx, status: int, body: dict):
    return fdk.response.Response(
        ctx,
        response_data=json.dumps(body),
        headers={"Content-Type": "application/json"},
        status_code=status,
    )


# ---------------------------------------------------------------------------
# Cliente de OCI Generative AI
# ---------------------------------------------------------------------------
def _call_genai(prompt: str, temperature: float, max_tokens: int) -> str:
    """Llama a OCI Generative AI y devuelve el texto generado."""

    # Modo mock para pruebas locales / CI
    if os.environ.get("MOCK_GENAI", "false").lower() == "true":
        logger.info("Mock GenAI activado")
        return f"[MOCK] Respuesta para: {prompt[:80]}"

    try:
        import oci  # noqa: PLC0415  — lazy import: 'oci' SDK is large and unavailable
        # in local/CI environments; importing at module level would break mock mode.

        region = os.environ["OCI_REGION"]
        compartment_id = os.environ["COMPARTMENT_ID"]
        model_id = os.environ["GENAI_MODEL_ID"]

        # Autenticación: Instance Principal cuando corre en OCI Functions
        signer = oci.auth.signers.get_resource_principals_signer()
        genai_client = oci.generative_ai_inference.GenerativeAiInferenceClient(
            config={},
            signer=signer,
            service_endpoint=(
                os.environ.get("GENAI_ENDPOINT")
                or f"https://inference.generativeai.{region}.oci.oraclecloud.com"
            ),
        )

        # Construcción de la petición para modelos de texto/chat
        chat_request = oci.generative_ai_inference.models.CohereChatRequest(
            message=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            is_stream=False,
        )

        chat_detail = oci.generative_ai_inference.models.ChatDetails(
            compartment_id=compartment_id,
            serving_mode=oci.generative_ai_inference.models.OnDemandServingMode(
                model_id=model_id,
            ),
            chat_request=chat_request,
        )

        response = genai_client.chat(chat_detail)
        chat_response = response.data.chat_response
        return chat_response.text

    except KeyError as exc:
        logger.error("Variable de entorno faltante: %s", exc)
        raise ValueError(f"Variable de entorno requerida no configurada: {exc}") from exc
    except Exception as exc:  # noqa: BLE001
        logger.error("Error al llamar a OCI GenAI: %s", exc)
        raise


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------
def _handle_health(ctx) -> fdk.response.Response:
    """GET /health — liveness probe."""
    return _json_response(
        ctx,
        200,
        {"status": "ok", "service": SERVICE_NAME, "version": VERSION},
    )


def _handle_agent(ctx, body: bytes) -> fdk.response.Response:
    """POST /agent — invoca el LLM y devuelve el resultado."""
    try:
        payload = json.loads(body or b"{}")
    except json.JSONDecodeError as exc:
        return _json_response(ctx, 400, {"error": f"JSON inválido: {exc}"})

    prompt = payload.get("prompt", "").strip()
    if not prompt:
        return _json_response(ctx, 400, {"error": "El campo 'prompt' es requerido."})

    temperature = float(payload.get("temperature", os.environ.get("TEMPERATURE", "0.7")))
    max_tokens = int(payload.get("max_tokens", os.environ.get("MAX_TOKENS", "1024")))
    session_id = payload.get("session_id", "")

    logger.info(
        "Invocando agente: session_id=%s, temperature=%s, max_tokens=%s",
        session_id,
        temperature,
        max_tokens,
    )

    try:
        result = _call_genai(prompt, temperature, max_tokens)
    except ValueError as exc:
        return _json_response(ctx, 500, {"error": str(exc)})
    except Exception as exc:  # noqa: BLE001
        return _json_response(ctx, 502, {"error": f"Error al invocar el modelo: {exc}"})

    response_body = {
        "response": result,
        "session_id": session_id,
        "model": os.environ.get("GENAI_MODEL_ID", "unknown"),
        "service": SERVICE_NAME,
    }
    logger.info("Respuesta generada correctamente: session_id=%s", session_id)
    return _json_response(ctx, 200, response_body)


# ---------------------------------------------------------------------------
# Entry point de OCI Functions (FDK)
# ---------------------------------------------------------------------------
def handler(ctx, data: io.BytesIO = None):
    """
    Entry point principal de la OCI Function.
    API Gateway inyecta la ruta en el header 'Fn-Http-Request-Url' o
    en el body como campo '__oci_path'. Se detecta la ruta para enrutar
    entre /agent y /health.
    """
    # Determinar ruta desde headers o URL
    headers = dict(ctx.Headers())
    request_url = headers.get("fn-http-request-url", headers.get("Fn-Http-Request-Url", "/agent"))
    method = headers.get("fn-http-method", headers.get("Fn-Http-Method", "POST")).upper()

    path = request_url.split("?")[0].rstrip("/") or "/agent"

    body = data.getvalue() if data else b""

    logger.info("Request: method=%s, path=%s", method, path)

    if path.endswith("/health") and method == "GET":
        return _handle_health(ctx)

    if path.endswith("/agent") and method == "POST":
        return _handle_agent(ctx, body)

    # Fallback: si se invoca directamente (sin API Gateway) asumir /agent POST
    if method == "POST" and body:
        return _handle_agent(ctx, body)

    return _json_response(ctx, 404, {"error": f"Ruta no encontrada: {method} {path}"})
