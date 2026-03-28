"""Claude API cleanup backend for Whisper Přepisovač.

Provides token counting, cost estimation, chunked transcript cleaning,
API key validation, and diff generation.
"""
from __future__ import annotations

import difflib
import threading
import time
from typing import Any

import anthropic

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CHUNK_CHARS = 80_000      # ~20k tokens — safely within 200k context window
OVERLAP_CHARS = 2_000     # overlap between chunks for context continuity

PRICING: dict[str, dict[str, float]] = {
    "claude-haiku-4-5": {"input": 1.0 / 1_000_000, "output": 5.0 / 1_000_000},
    "claude-sonnet-4-5": {"input": 3.0 / 1_000_000, "output": 15.0 / 1_000_000},
}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def clean_transcript(
    text: str,
    system_prompt: str,
    context_text: str,
    model: str,
    api_key: str,
    progress_queue: Any,
    task_id: str,
    timeout: float = 300.0,
) -> dict:
    """Send *text* to the Claude API for cleanup.

    Args:
        text: Raw transcript text to clean.
        system_prompt: Claude system prompt.
        context_text: Optional user-provided context (prepended to the message).
        model: Model identifier (e.g. "claude-haiku-4-5").
        api_key: Anthropic API key.
        progress_queue: Queue for progress messages sent to the UI.
        task_id: Unique file identifier for UI queue messages.
        timeout: Per-call timeout in seconds (default 300).

    Returns:
        dict with keys: "result" (str), "input_tokens" (int), "output_tokens" (int).

    Raises:
        anthropic.AuthenticationError: on invalid API key.
        anthropic.APIStatusError: on other API errors.
        TimeoutError: when *timeout* is exceeded.
    """
    client = anthropic.Anthropic(api_key=api_key)

    chunks = _split_into_chunks(text)
    total_chunks = len(chunks)
    total_input_tokens = 0
    total_output_tokens = 0
    results: list[str] = []

    for i, chunk in enumerate(chunks):
        # Build user message
        if context_text and context_text.strip():
            user_msg = f"Context: {context_text.strip()}\n\n---\n\n{chunk}"
        else:
            user_msg = chunk

        # Progress notification
        if total_chunks > 1:
            progress_queue.put({
                "type": "claude_chunk",
                "task_id": task_id,
                "n": i + 1,
                "total": total_chunks,
            })
        else:
            progress_queue.put({
                "type": "claude_processing",
                "task_id": task_id,
            })

        # Slow-call watchdog: notify after 60 s
        call_start = time.monotonic()
        watchdog_fired = threading.Event()

        def _watchdog(start: float = call_start, event: threading.Event = watchdog_fired) -> None:
            time.sleep(60)
            if not event.is_set():
                elapsed = int(time.monotonic() - start)
                progress_queue.put({
                    "type": "claude_slow",
                    "task_id": task_id,
                    "elapsed": elapsed,
                })

        t = threading.Thread(target=_watchdog, daemon=True)
        t.start()

        try:
            response = client.messages.create(
                model=model,
                max_tokens=64_000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_msg}],
                timeout=timeout,
            )
        except anthropic.AuthenticationError:
            watchdog_fired.set()
            raise anthropic.AuthenticationError(
                message="Invalid API key",
                response=None,  # type: ignore[arg-type]
                body=None,
            )
        except anthropic.APIStatusError:
            watchdog_fired.set()
            raise
        except Exception as exc:
            watchdog_fired.set()
            if "timeout" in str(exc).lower() or "timed out" in str(exc).lower():
                raise TimeoutError(f"Timeout after {timeout}s") from exc
            raise
        finally:
            watchdog_fired.set()

        total_input_tokens += response.usage.input_tokens
        total_output_tokens += response.usage.output_tokens
        results.append(response.content[0].text)

    merged = _merge_chunks(results) if len(results) > 1 else results[0]
    return {
        "result": merged,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
    }


def validate_api_key(api_key: str) -> tuple[bool, str]:
    """Validate *api_key* with a minimal test call.

    Returns:
        (True, "") on success.
        (True, "") on rate-limit (429 / 529) — key is still valid.
        (False, error_msg) on authentication failure or other API error.
    """
    client = anthropic.Anthropic(api_key=api_key)
    try:
        client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1,
            messages=[{"role": "user", "content": "ping"}],
        )
        return (True, "")
    except anthropic.AuthenticationError:
        return (False, "Invalid API key — check the value")
    except anthropic.APIStatusError as exc:
        if exc.status_code in (429, 529):
            # Rate limited — key is valid
            return (True, "")
        return (False, f"API error {exc.status_code}: {exc.message}")


def estimate_cost_pre_send(char_count: int, model: str) -> float:
    """Estimate API cost before sending, using character-count heuristic.

    Approximation: 4 chars ≈ 1 input token; output ≈ 80 % of input.
    """
    p = PRICING.get(model, PRICING["claude-haiku-4-5"])
    estimated_input_tokens = char_count / 4
    estimated_output_tokens = estimated_input_tokens * 0.8
    return estimated_input_tokens * p["input"] + estimated_output_tokens * p["output"]


def calculate_actual_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    """Calculate exact API cost from actual token usage."""
    p = PRICING.get(model, PRICING["claude-haiku-4-5"])
    return input_tokens * p["input"] + output_tokens * p["output"]


def generate_diff(original: str, cleaned: str) -> str:
    """Return a unified diff comparing *original* and *cleaned* transcripts."""
    diff_lines = difflib.unified_diff(
        original.splitlines(keepends=True),
        cleaned.splitlines(keepends=True),
        fromfile="Original",
        tofile="Cleaned",
        lineterm="",
    )
    return "".join(diff_lines)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _split_into_chunks(text: str) -> list[str]:
    """Split *text* into overlapping chunks of at most CHUNK_CHARS characters.

    Prefers to split at paragraph boundaries (double newline) when possible.
    Consecutive chunks overlap by OVERLAP_CHARS for context continuity.
    """
    if len(text) <= CHUNK_CHARS:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + CHUNK_CHARS
        if end >= len(text):
            chunks.append(text[start:])
            break

        # Prefer a paragraph break near the boundary
        split_pos = text.rfind("\n\n", start, end)
        if split_pos == -1 or split_pos <= start:
            # Fall back to hard boundary
            split_pos = end

        chunks.append(text[start:split_pos])
        # Next chunk starts OVERLAP_CHARS before the split point
        start = max(split_pos - OVERLAP_CHARS, split_pos)

    return chunks


def _merge_chunks(parts: list[str]) -> str:
    """Merge cleaned chunk results with a separator."""
    return "\n\n---\n\n".join(parts)
