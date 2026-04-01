"""
AXONHIS Virtual Avatar – FastAPI Routes.

Endpoints:
  POST /avatar/sessions                    – Create session
  POST /avatar/sessions/{id}/converse      – Full pipeline (STT → LLM → workflow → TTS)
  POST /avatar/sessions/{id}/chat          – Text-only chat
  POST /avatar/sessions/{id}/speech-to-text – STT only
  POST /avatar/sessions/{id}/text-to-speech – TTS only
  GET  /avatar/sessions/{id}/messages      – Conversation history
  DELETE /avatar/sessions/{id}             – End session
  GET  /avatar/admin/workflows             – List workflow configs
  PUT  /avatar/admin/workflows/{id}        – Update workflow config
  GET  /avatar/admin/analytics             – Usage analytics
  GET  /avatar/admin/logs                  – Conversation logs
"""
import uuid

from fastapi import APIRouter, HTTPException, Query

from app.dependencies import CurrentUser, DBSession
from app.core.avatar.schemas import (
    AvatarAnalyticsOut,
    AvatarChatRequest,
    AvatarChatResponse,
    AvatarConverseRequest,
    AvatarConverseResponse,
    AvatarMessageOut,
    AvatarSessionCreate,
    AvatarSessionOut,
    AvatarSTTRequest,
    AvatarSTTResponse,
    AvatarTTSRequest,
    AvatarTTSResponse,
    AvatarWorkflowConfigOut,
    AvatarWorkflowConfigUpdate,
)
from app.core.avatar.services import (
    AvatarSessionService,
    ConversationService,
    SpeechService,
    WorkflowOrchestrator,
)

router = APIRouter(prefix="/avatar", tags=["Virtual Avatar – Interaction Layer"])


# ─────────────────────────────────────────────────────────────────────────────
# Session Management
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/sessions", response_model=AvatarSessionOut, status_code=201)
async def create_session(
    body: AvatarSessionCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> AvatarSessionOut:
    """Create a new avatar conversation session."""
    svc = AvatarSessionService(db)
    session = await svc.create_session(user_id=current_user.id, language=body.language)

    # Auto-generate greeting
    greeting_map = {
        "en": "Hello! I'm Dr. AXON, your virtual healthcare assistant. How can I help you today?",
        "hi": "नमस्ते! मैं डॉ. AXON हूँ, आपका वर्चुअल स्वास्थ्य सहायक। मैं आज आपकी कैसे सहायता कर सकता हूँ?",
        "mr": "नमस्कार! मी डॉ. AXON आहे, तुमचा व्हर्च्युअल आरोग्य सहाय्यक. मी आज तुम्हाला कशी मदत करू शकतो?",
        "es": "¡Hola! Soy el Dr. AXON, su asistente virtual de salud. ¿Cómo puedo ayudarle hoy?",
        "de": "Hallo! Ich bin Dr. AXON, Ihr virtueller Gesundheitsassistent. Wie kann ich Ihnen heute helfen?",
        "fr": "Bonjour ! Je suis le Dr AXON, votre assistant de santé virtuel. Comment puis-je vous aider aujourd'hui ?",
        "ar": "مرحباً! أنا الدكتور AXON، مساعدك الصحي الافتراضي. كيف يمكنني مساعدتك اليوم؟",
        "zh": "您好！我是AXON医生，您的虚拟健康助手。今天我能为您做什么？",
        "ja": "こんにちは！私はAXON先生です。あなたのバーチャルヘルスアシスタントです。今日はどのようにお手伝いできますか？",
        "pt": "Olá! Sou o Dr. AXON, seu assistente virtual de saúde. Como posso ajudá-lo hoje?",
        "ru": "Здравствуйте! Я доктор AXON, ваш виртуальный помощник по здоровью. Чем я могу вам помочь сегодня?",
    }
    greeting = greeting_map.get(body.language, greeting_map["en"])
    await svc.add_message(session.id, role="assistant", content=greeting)

    # Generate TTS for greeting
    try:
        speech_svc = SpeechService()
        audio = await speech_svc.text_to_speech(greeting, body.language)
    except Exception:
        audio = None

    await db.refresh(session)
    out = AvatarSessionOut.model_validate(session)
    return out


@router.delete("/sessions/{session_id}", status_code=204)
async def end_session(
    session_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> None:
    """End an avatar session."""
    svc = AvatarSessionService(db)
    session = await svc.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await svc.end_session(session_id)


# ─────────────────────────────────────────────────────────────────────────────
# Full Conversation Pipeline
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/sessions/{session_id}/converse", response_model=AvatarConverseResponse)
async def converse(
    session_id: uuid.UUID,
    body: AvatarConverseRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> AvatarConverseResponse:
    """Full pipeline: Speech-to-Text → LLM → Workflow → Text-to-Speech."""
    session_svc = AvatarSessionService(db)
    session = await session_svc.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Step 1: Speech-to-Text
    speech_svc = SpeechService()
    try:
        stt_result = await speech_svc.speech_to_text(body.audio_base64, session.language)
        transcription = stt_result["transcription"]
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Speech recognition failed: {e}") from e

    if not transcription:
        return AvatarConverseResponse(
            transcription="",
            response_text="I couldn't understand that. Could you please speak again?",
        )

    # Save user message
    await session_svc.add_message(session_id, role="user", content=transcription)

    # Step 2: LLM Processing
    conv_svc = ConversationService(db)
    llm_result = await conv_svc.process_message(session_id, transcription, session.language)

    # Step 3: Workflow Execution
    workflow_status = None
    if llm_result.get("intent"):
        orchestrator = WorkflowOrchestrator(db)
        workflow_status = await orchestrator.execute(
            session, llm_result["intent"], llm_result.get("entities", {})
        )

    # Save assistant message
    await session_svc.add_message(
        session_id,
        role="assistant",
        content=llm_result["response_text"],
        intent=llm_result.get("intent"),
        workflow=llm_result.get("workflow"),
        entities=llm_result.get("entities"),
    )

    # Step 4: Text-to-Speech
    audio_b64 = None
    try:
        audio_b64 = await speech_svc.text_to_speech(llm_result["response_text"], session.language)
    except Exception:
        pass  # Graceful fallback — frontend can use browser TTS

    return AvatarConverseResponse(
        transcription=transcription,
        response_text=llm_result["response_text"],
        audio_base64=audio_b64,
        intent=llm_result.get("intent"),
        workflow=llm_result.get("workflow"),
        workflow_status=workflow_status,
        entities=llm_result.get("entities"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Text Chat (fallback / testing)
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/sessions/{session_id}/chat", response_model=AvatarChatResponse)
async def chat_text(
    session_id: uuid.UUID,
    body: AvatarChatRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> AvatarChatResponse:
    """Text-only chat without speech processing."""
    session_svc = AvatarSessionService(db)
    session = await session_svc.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save user message
    await session_svc.add_message(session_id, role="user", content=body.text)

    # LLM Processing
    conv_svc = ConversationService(db)
    llm_result = await conv_svc.process_message(session_id, body.text, session.language)

    # Workflow Execution
    workflow_status = None
    if llm_result.get("intent"):
        orchestrator = WorkflowOrchestrator(db)
        workflow_status = await orchestrator.execute(
            session, llm_result["intent"], llm_result.get("entities", {})
        )

    # Save assistant message
    await session_svc.add_message(
        session_id,
        role="assistant",
        content=llm_result["response_text"],
        intent=llm_result.get("intent"),
        workflow=llm_result.get("workflow"),
        entities=llm_result.get("entities"),
    )

    # TTS
    audio_b64 = None
    try:
        speech_svc = SpeechService()
        audio_b64 = await speech_svc.text_to_speech(llm_result["response_text"], session.language)
    except Exception:
        pass

    return AvatarChatResponse(
        response_text=llm_result["response_text"],
        audio_base64=audio_b64,
        intent=llm_result.get("intent"),
        workflow=llm_result.get("workflow"),
        workflow_status=workflow_status,
        entities=llm_result.get("entities"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Standalone STT / TTS
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/sessions/{session_id}/speech-to-text", response_model=AvatarSTTResponse)
async def speech_to_text(
    session_id: uuid.UUID,
    body: AvatarSTTRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> AvatarSTTResponse:
    """Convert speech audio to text."""
    session_svc = AvatarSessionService(db)
    session = await session_svc.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    speech_svc = SpeechService()
    result = await speech_svc.speech_to_text(body.audio_base64, session.language)
    return AvatarSTTResponse(**result)


@router.post("/sessions/{session_id}/text-to-speech", response_model=AvatarTTSResponse)
async def text_to_speech(
    session_id: uuid.UUID,
    body: AvatarTTSRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> AvatarTTSResponse:
    """Convert text to speech audio."""
    session_svc = AvatarSessionService(db)
    session = await session_svc.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    speech_svc = SpeechService()
    audio_b64 = await speech_svc.text_to_speech(body.text, body.language)
    return AvatarTTSResponse(audio_base64=audio_b64, language=body.language)


# ─────────────────────────────────────────────────────────────────────────────
# Message History
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/sessions/{session_id}/messages", response_model=list[AvatarMessageOut])
async def get_messages(
    session_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> list[AvatarMessageOut]:
    """Get all messages for a session."""
    svc = AvatarSessionService(db)
    messages = await svc.get_messages(session_id)
    return [AvatarMessageOut.model_validate(m) for m in messages]


# ─────────────────────────────────────────────────────────────────────────────
# Admin Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/admin/workflows", response_model=list[AvatarWorkflowConfigOut])
async def list_workflow_configs(
    db: DBSession,
    current_user: CurrentUser,
) -> list[AvatarWorkflowConfigOut]:
    """List all avatar workflow configurations."""
    svc = AvatarSessionService(db)
    configs = await svc.get_workflow_configs()
    return [AvatarWorkflowConfigOut.model_validate(c) for c in configs]


@router.put("/admin/workflows/{config_id}", response_model=AvatarWorkflowConfigOut)
async def update_workflow_config(
    config_id: uuid.UUID,
    body: AvatarWorkflowConfigUpdate,
    db: DBSession,
    current_user: CurrentUser,
) -> AvatarWorkflowConfigOut:
    """Update a workflow configuration."""
    svc = AvatarSessionService(db)
    cfg = await svc.update_workflow_config(config_id, body.model_dump(exclude_unset=True))
    if not cfg:
        raise HTTPException(status_code=404, detail="Config not found")
    return AvatarWorkflowConfigOut.model_validate(cfg)


@router.get("/admin/analytics", response_model=AvatarAnalyticsOut)
async def get_analytics(
    db: DBSession,
    current_user: CurrentUser,
) -> AvatarAnalyticsOut:
    """Get avatar usage analytics."""
    svc = AvatarSessionService(db)
    data = await svc.get_analytics()
    return AvatarAnalyticsOut(**data)


@router.get("/admin/logs")
async def get_conversation_logs(
    db: DBSession,
    current_user: CurrentUser,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    """Get conversation logs for admin review."""
    svc = AvatarSessionService(db)
    return await svc.get_conversation_logs(limit=limit, offset=offset)
