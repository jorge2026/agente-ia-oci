"""
OCI Function — Agente de IA
Recibe peticiones JSON con 'prompt' y llama a OCI Generative AI.
"""

import io
import json
import logging
import os
import sys
from functools import lru_cache

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
DEFAULT_MAX_PROMPT_CHARS = 5000
DEFAULT_MAX_TOKENS_LIMIT = 4096
DEFAULT_MIN_TEMPERATURE = 0.0
DEFAULT_MAX_TEMPERATURE = 2.0


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
# Validación de payload
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _read_int_env(name: str, default: int) -> int:
    raw_value = os.environ.get(name, str(default))
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"Variable de entorno inválida: {name}={raw_value}") from exc


def _read_float_env(name: str, default: float) -> float:
    raw_value = os.environ.get(name, str(default))
    try:
        return float(raw_value)
    except ValueError as exc:
        raise ValueError(f"Variable de entorno inválida: {name}={raw_value}") from exc


def _load_validation_limits() -> dict[str, float | int]:
    max_prompt_chars = _read_int_env("MAX_PROMPT_CHARS", DEFAULT_MAX_PROMPT_CHARS)
    max_tokens_limit = _read_int_env("MAX_TOKENS_LIMIT", DEFAULT_MAX_TOKENS_LIMIT)
    min_temperature = _read_float_env("MIN_TEMPERATURE", DEFAULT_MIN_TEMPERATURE)
    max_temperature = _read_float_env("MAX_TEMPERATURE", DEFAULT_MAX_TEMPERATURE)
    default_temperature = _read_float_env("TEMPERATURE", 0.7)
    default_max_tokens = _read_int_env("MAX_TOKENS", 1024)

    if max_prompt_chars < 1:
        raise ValueError(f"MAX_PROMPT_CHARS={max_prompt_chars} debe ser >= 1.")
    if max_tokens_limit < 1:
        raise ValueError(f"MAX_TOKENS_LIMIT={max_tokens_limit} debe ser >= 1.")
    if min_temperature > max_temperature:
        raise ValueError("MIN_TEMPERATURE no puede ser mayor que MAX_TEMPERATURE.")
    if not min_temperature <= default_temperature <= max_temperature:
        raise ValueError(
            f"TEMPERATURE={default_temperature} fuera del rango permitido ({min_temperature}-{max_temperature})."
        )
    if default_max_tokens < 1 or default_max_tokens > max_tokens_limit:
        raise ValueError(
            f"MAX_TOKENS={default_max_tokens} fuera del rango permitido (1-{max_tokens_limit})."
        )

    return {
        "max_prompt_chars": max_prompt_chars,
        "max_tokens_limit": max_tokens_limit,
        "min_temperature": min_temperature,
        "max_temperature": max_temperature,
        "default_temperature": default_temperature,
        "default_max_tokens": default_max_tokens,
    }


def _validate_payload(payload: dict) -> tuple[dict | None, list[str]]:
    if not isinstance(payload, dict):
        return None, ["El cuerpo debe ser un objeto JSON."]

    limits = _load_validation_limits()
    max_prompt_chars = limits["max_prompt_chars"]
    max_tokens_limit = limits["max_tokens_limit"]
    min_temperature = limits["min_temperature"]
    max_temperature = limits["max_temperature"]
    default_temperature = limits["default_temperature"]
    default_max_tokens = limits["default_max_tokens"]
    errors = []

    prompt_value = payload.get("prompt")
    if not isinstance(prompt_value, str) or not prompt_value.strip():
        errors.append("El campo 'prompt' es requerido y debe ser texto.")
        prompt = ""
    else:
        prompt = prompt_value.strip()
        if len(prompt) > max_prompt_chars:
            errors.append(f"El campo 'prompt' supera el máximo de {max_prompt_chars} caracteres.")

    temperature = None
    temperature_value = payload.get("temperature", default_temperature)
    try:
        temperature = float(temperature_value)
    except (TypeError, ValueError):
        errors.append("temperature debe ser numérico.")
    else:
        if not min_temperature <= temperature <= max_temperature:
            errors.append(f"temperature debe estar entre {min_temperature} y {max_temperature}.")

    max_tokens = None
    max_tokens_value = payload.get("max_tokens", default_max_tokens)
    try:
        max_tokens = int(max_tokens_value)
    except (TypeError, ValueError):
        errors.append("max_tokens debe ser un entero.")
    else:
        if max_tokens < 1 or max_tokens > max_tokens_limit:
            errors.append(f"max_tokens debe estar entre 1 y {max_tokens_limit}.")

    session_id = payload.get("session_id")
    if session_id is None:
        session_id = ""
    if not isinstance(session_id, str):
        errors.append("session_id debe ser texto.")

    if errors:
        return None, errors

    return {
        "prompt": prompt,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "session_id": session_id,
    }, []


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

    try:
        validated, errors = _validate_payload(payload)
    except ValueError as exc:
        return _json_response(ctx, 500, {"error": str(exc)})

    if errors:
        return _json_response(ctx, 400, {"error": "Validación fallida.", "details": errors})

    prompt = validated["prompt"]
    temperature = validated["temperature"]
    max_tokens = validated["max_tokens"]
    session_id = validated["session_id"]

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
