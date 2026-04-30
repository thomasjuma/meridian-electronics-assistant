import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.core.agent import Support
from app.schemas import ChatRequest, ChatResponse
from app.chat_service import load_conversation, save_conversation

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())
        conversation = load_conversation(session_id)

        messages = [{"role": "system", "content": "You are a helpful customer support assistant."}]

        for msg in conversation[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": request.message})

        support_agent = Support(name="Meridian Support")
        response = await support_agent.run_chat(messages)
        print(f"Response: {response}")
        assistant_response = response.final_output
        print(f"Assistant response: {assistant_response}")
        conversation.append(
            {"role": "user", "content": request.message, "timestamp": datetime.now().isoformat()}
        )
        conversation.append(
            {
                "role": "assistant",
                "content": assistant_response,
                "timestamp": datetime.now().isoformat(),
            }
        )

        save_conversation(session_id, conversation)

        return ChatResponse(history=conversation, response=assistant_response, session_id=session_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation/{session_id}")
async def get_conversation(session_id: str):
    try:
        conversation = load_conversation(session_id)
        return {"session_id": session_id, "messages": conversation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    return {
        "status": "healthy", 
        "use_s3": "USE_S3",
        "bedrock_model": "BEDROCK_MODEL_ID",
    }
