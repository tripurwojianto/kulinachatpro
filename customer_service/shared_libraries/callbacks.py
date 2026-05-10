"""Callback functions untuk Delisa - Lazizah Aqiqah."""

import logging
import time

from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai.types import Content, Part

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

RATE_LIMIT_SECS = 60
RPM_QUOTA = 10


def rate_limit_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> LlmResponse | None:
    """
    Rate limiter + fallback ke OpenAI saat Gemini 429.
    """
    # Pastikan tidak ada part kosong
    for content in llm_request.contents:
        for part in content.parts:
            if hasattr(part, "text") and part.text == "":
                part.text = " "

    now = time.time()

    # Cek apakah sedang dalam mode fallback OpenAI
    if callback_context.state.get("use_openai_fallback"):
        return _openai_fallback(llm_request)

    # Rate limiting logic
    if "timer_start" not in callback_context.state:
        callback_context.state["timer_start"] = now
        callback_context.state["request_count"] = 1
        return None

    request_count = callback_context.state["request_count"] + 1
    elapsed_secs = now - callback_context.state["timer_start"]

    logger.debug(
        "rate_limit [count: %i, elapsed: %is]",
        request_count, elapsed_secs
    )

    if request_count > RPM_QUOTA:
        delay = RATE_LIMIT_SECS - elapsed_secs + 1
        if delay > 0:
            logger.debug("Rate limit: sleep %is", delay)
            time.sleep(delay)
        callback_context.state["timer_start"] = now
        callback_context.state["request_count"] = 1
    else:
        callback_context.state["request_count"] = request_count

    return None


def _openai_fallback(llm_request: LlmRequest) -> LlmResponse | None:
    """
    Kirim request ke OpenAI saat Gemini 429.
    Return LlmResponse atau None jika gagal.
    """
    try:
        import os
        import json
        import urllib.request

        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            logger.warning("[Fallback] OPENAI_API_KEY tidak ditemukan di .env")
            return None

        # Ambil pesan terakhir dari request
        messages = []
        for content in llm_request.contents:
            role = "user" if content.role == "user" else "assistant"
            text = " ".join(
                p.text for p in content.parts if hasattr(p, "text") and p.text
            )
            if text.strip():
                messages.append({"role": role, "content": text})

        # Tambah system prompt jika ada
        system = llm_request.config.system_instruction if llm_request.config else None
        if system:
            system_text = " ".join(
                p.text for p in system.parts if hasattr(p, "text")
            ) if hasattr(system, "parts") else str(system)
            messages.insert(0, {"role": "system", "content": system_text})

        payload = json.dumps({
            "model": "gpt-4o",
            "messages": messages,
            "max_tokens": 1000,
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        reply = data["choices"][0]["message"]["content"]
        logger.info("[Fallback] OpenAI berhasil menjawab.")

        return LlmResponse(
            content=Content(
                role="model",
                parts=[Part(text=f"[via GPT-4o]\n{reply}")]
            )
        )

    except Exception as e:
        logger.error("[Fallback] OpenAI error: %s", str(e))
        return None


def handle_gemini_429(callback_context: CallbackContext) -> str:
    """
    Dipanggil manual saat terdeteksi error 429.
    Aktifkan flag fallback OpenAI.
    """
    callback_context.state["use_openai_fallback"] = True
    logger.warning("[429] Gemini quota habis — beralih ke OpenAI GPT-4o")
    return "Gemini quota habis. Delisa beralih ke GPT-4o otomatis."


def reset_to_gemini(callback_context: CallbackContext) -> str:
    """Reset fallback — kembali ke Gemini."""
    callback_context.state["use_openai_fallback"] = False
    logger.info("[Reset] Kembali ke Gemini.")
    return "Kembali ke Gemini."


def before_tool(tool: BaseTool, args: dict, tool_context: CallbackContext):
    """Validasi ringan sebelum tool dipanggil."""
    logger.debug("[before_tool] %s args: %s", tool.name, args)
    return None


def after_tool(
    tool: BaseTool,
    args: dict,
    tool_context: ToolContext,
    tool_response: dict,
) -> dict | None:
    """Log hasil tool."""
    logger.debug("[after_tool] %s response: %s", tool.name, tool_response)
    return None


def before_agent(callback_context: InvocationContext):
    """Inisialisasi state sesi."""
    if "use_openai_fallback" not in callback_context.state:
        callback_context.state["use_openai_fallback"] = False
    if "request_count" not in callback_context.state:
        callback_context.state["request_count"] = 0
