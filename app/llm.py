#llama3.1:latest       4.9 GB
#qwen3.5:latest.       6.6 GB
#gemma3:12b-it-qat     8.9 GB
#mistral-small:latest   14 GB 
#llm.py
"""
Centralized LLM interface.

Public API:

    text = generate(prompt)

No other module should call Ollama directly.
"""

from time import perf_counter
import logging

from ollama import chat


logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------

MODELS = {
    "fast": "llama3.1:latest",
    "smart": "mistral-small:latest",
    "deep": "gemma3:12b-it-qat",
}

DEFAULT_MODEL = MODELS["fast"]

MODEL_ROUTING = {
    "planner": "fast",
    "worker": "fast",
    "analyst": "fast",
    "report": "deep",
    "repair": "fast",
    "conflict": "deep",
}

DEBUG = False


# ------------------------------------------------------------------
# Internal helper
# ------------------------------------------------------------------

def _call_model(
    model_name: str,
    prompt: str,
    temperature: float,
    max_tokens: int,
) -> str | None:

    start = perf_counter()

    response = chat(
        model=model_name,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        options={
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    )

    elapsed = perf_counter() - start

    if DEBUG:
        logger.debug("=" * 80)
        logger.debug("MODEL: %s", model_name)
        logger.debug(response)
        logger.debug("=" * 80)

    logger.info(
        "LLM | model=%s | %.2fs | reason=%s",
        model_name,
        elapsed,
        getattr(response, "done_reason", "unknown"),
    )

    content = response.message.content

    if content and content.strip():
        return content.strip()

    done_reason = getattr(response, "done_reason", "")

    if done_reason == "length":
        logger.warning(
            "%s exhausted token budget before producing final answer.",
            model_name,
        )
    else:
        logger.warning(
            "%s returned empty content.",
            model_name,
        )

    return None


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def generate(
    prompt: str,
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 4096,
) -> str:

    model_name = MODELS.get(model, model) if model else DEFAULT_MODEL

    try:

        response = _call_model(
            model_name=model_name,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if response:
            return response

    except Exception as e:

        logger.exception(
            "LLM call failed (%s): %s",
            model_name,
            e,
        )

    # Don't retry if we're already using the fallback model.
    if model_name == DEFAULT_MODEL:

        logger.error(
            "Default model (%s) failed.",
            DEFAULT_MODEL,
        )

        return ""

    logger.warning(
        "Falling back from %s → %s",
        model_name,
        DEFAULT_MODEL,
    )

    try:

        response = _call_model(
            model_name=DEFAULT_MODEL,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response or ""

    except Exception as e:

        logger.exception(
            "Fallback model failed (%s): %s",
            DEFAULT_MODEL,
            e,
        )

        return ""