"""AI caregiver assistant, backed by the Claude API.

Streams via Server-Sent Events so the frontend chat widget can render tokens
as they arrive. The API key never reaches the browser — it's read
server-side from ANTHROPIC_API_KEY (see backend/.env.example). If it's not
set, /chat returns a 503 with setup instructions instead of failing opaquely.
"""
import json
import os

import anthropic
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.auth import get_current_user

router = APIRouter(prefix="/api/assistant", tags=["assistant"], dependencies=[Depends(get_current_user)])

MODEL = "claude-opus-5"

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
    return {"configured": bool(os.environ.get("ANTHROPIC_API_KEY"))}


@router.post("/chat")
def chat(payload: ChatRequest):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail=(
                "AI Assistant isn't configured. Add ANTHROPIC_API_KEY to backend/.env "
                "(see backend/.env.example) and restart the backend."
            ),
        )

    client = anthropic.Anthropic(api_key=api_key)
    system = _build_system(payload.patient_context)
    messages = [{"role": m.role, "content": m.content} for m in payload.messages]

    def event_stream():
        try:
            with client.messages.stream(
                model=MODEL,
                max_tokens=1536,
                system=system,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {json.dumps({'text': text})}\n\n"
            yield "data: [DONE]\n\n"
        except anthropic.APIStatusError as e:
            yield f"data: {json.dumps({'error': f'API error ({e.status_code}): {e.message}'})}\n\n"
        except anthropic.APIConnectionError:
            yield f"data: {json.dumps({'error': 'Could not reach the Claude API. Check network connectivity.'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
