"""AI caregiver assistant, backed by Claude and/or Gemini — the frontend
picks whichever provider(s) are configured.

Streams via Server-Sent Events so the frontend chat widget can render
tokens as they arrive. API keys never reach the browser — they're read
server-side from ANTHROPIC_API_KEY / GEMINI_API_KEY (see
backend/.env.example). If a requested provider isn't configured, /chat
returns a 503 with setup instructions instead of failing opaquely.
"""
import json
import os

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.auth import get_current_user

router = APIRouter(prefix="/api/assistant", tags=["assistant"], dependencies=[Depends(get_current_user)])

CLAUDE_MODEL = "claude-opus-5"
GEMINI_MODEL = "gemini-3.7-flash"

SYSTEM_PROMPT = """You are the caregiver-facing AI assistant embedded in BrainTriage, an \
adaptive Alzheimer's diagnostic triage prototype (Precision Care Challenge 2026, built \
for review by RINPAS — a neuropsychiatry institute in Ranchi, India).

Your job: answer questions from caregivers, family members, and clinicians about \
Alzheimer's disease, dementia, cognitive symptoms, and how to interpret this app's \
output — in plain, warm, non-alarmist language.

Hard rules:
- You are NOT a diagnostic tool and do not provide a diagnosis, prescribe treatment, or \
give personalized medical advice. Always recommend consulting a qualified doctor or \
neurologist for actual clinical decisions.
- If a message describes a genuine medical emergency (chest pain, stroke symptoms, \
suicidal ideation, severe confusion with injury risk, etc.), your first line must tell \
them to call their local emergency number immediately — do not attempt to triage it \
yourself.
- If asked about this specific patient's risk result (when patient context is provided \
below), explain what the numbers mean and why, grounded ONLY in the data given — never \
invent lab values, scan findings, or history not present in the context.
- Keep answers concise and skimmable (short paragraphs, occasional bullet points) — \
caregivers are often reading this while stressed or busy.
"""


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    patient_context: dict | None = None
    provider: str = "claude"  # "claude" | "gemini"


def _build_system(patient_context: dict | None) -> str:
    if not patient_context:
        return SYSTEM_PROMPT
    return (
        SYSTEM_PROMPT
        + "\n\nCurrent patient context (from this session's triage run — use only this, "
        "don't invent anything beyond it):\n"
        + json.dumps(patient_context, indent=2)
    )


@router.get("/status")
def status():
    return {
        "configured": bool(os.environ.get("ANTHROPIC_API_KEY")),  # kept for back-compat
        "providers": {
            "claude": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "gemini": bool(os.environ.get("GEMINI_API_KEY")),
        },
    }


def _stream_claude(api_key: str, system: str, messages: list[dict]):
    client = anthropic.Anthropic(api_key=api_key)
    try:
        with client.messages.stream(
            model=CLAUDE_MODEL,
            max_tokens=1536,
            system=system,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {json.dumps({'text': text})}\n\n"
        yield "data: [DONE]\n\n"
    except anthropic.APIStatusError as e:
        yield f"data: {json.dumps({'error': f'Claude API error ({e.status_code}): {e.message}'})}\n\n"
    except anthropic.APIConnectionError:
        yield f"data: {json.dumps({'error': 'Could not reach the Claude API. Check network connectivity.'})}\n\n"


def _stream_gemini(api_key: str, system: str, messages: list[dict]):
    # Gemini's Interactions API is stateful (multi-turn via previous_interaction_id
    # chaining) rather than stateless-with-full-history like Claude's Messages API.
    # We already resend the whole conversation from the frontend each request (to
    # stay symmetric with the Claude path and avoid persisting Gemini-specific
    # interaction IDs server-side), so history is flattened into one prompt instead.
    from google import genai

    client = genai.Client(api_key=api_key)
    transcript = "\n\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages)

    # What looked like ~50% of calls silently returning empty turned out to
    # be quota_exceeded events on the free tier (20 req/min for this model)
    # — the stream emits an explicit event_type="error" in that case, which
    # earlier code never checked for, so it read as an unexplained blank
    # response instead of the real, actionable error. Quota errors aren't
    # worth retrying (that only burns through the limit faster and the API
    # already tells us how long to wait); a genuinely empty stream with no
    # error event at all gets one bounded retry.
    MAX_ATTEMPTS = 2
    try:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            stream = client.interactions.create(
                model=GEMINI_MODEL,
                system_instruction=system,
                input=transcript,
                stream=True,
            )
            got_text = False
            stream_error = None
            for event in stream:
                event_type = getattr(event, "event_type", None)
                if event_type == "step.delta":
                    delta = getattr(event, "delta", None)
                    if delta is not None and getattr(delta, "type", None) == "text":
                        got_text = True
                        yield f"data: {json.dumps({'text': delta.text})}\n\n"
                elif event_type == "error":
                    err = getattr(event, "error", None)
                    stream_error = getattr(err, "message", None) or str(err)
            if got_text:
                yield "data: [DONE]\n\n"
                return
            if stream_error:
                yield f"data: {json.dumps({'error': f'Gemini API error: {stream_error}'})}\n\n"
                return
        yield f"data: {json.dumps({'error': f'Gemini returned an empty response after {MAX_ATTEMPTS} attempts — please try again.'})}\n\n"
    except Exception as e:
        # The interactions API's error classes live in a private module
        # (google.genai._gaos.lib.compat_errors), not the public `errors`
        # module — pull the useful bits off duck-typed attributes instead
        # of importing a private path that could shift under us.
        status_code = getattr(e, "status_code", None)
        message = getattr(e, "message", None) or str(e)
        prefix = f"Gemini API error ({status_code})" if status_code else "Could not reach the Gemini API"
        yield f"data: {json.dumps({'error': f'{prefix}: {message}'})}\n\n"


@router.post("/chat")
def chat(payload: ChatRequest):
    provider = payload.provider if payload.provider in ("claude", "gemini") else "claude"
    env_key = "ANTHROPIC_API_KEY" if provider == "claude" else "GEMINI_API_KEY"
    api_key = os.environ.get(env_key)
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail=(
                f"The {provider.capitalize()} provider isn't configured. Add {env_key} to "
                "backend/.env (see backend/.env.example) and restart the backend."
            ),
        )

    system = _build_system(payload.patient_context)
    messages = [{"role": m.role, "content": m.content} for m in payload.messages]

    stream_fn = _stream_claude if provider == "claude" else _stream_gemini
    return StreamingResponse(stream_fn(api_key, system, messages), media_type="text/event-stream")
