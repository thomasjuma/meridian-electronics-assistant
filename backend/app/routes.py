import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException

from schemas import OrderCreate, OrderUpdate, ChatRequest, ChatResponse
from database import get_db
from repository import OrderRepository
from sqlalchemy.orm import Session
from fastapi import Depends
from core.agent import agent_chat
from services import services
from services.chat import load_conversation, save_conversation

app = FastAPI(title="Order Management API")

def get_orders_repository(db: Session = Depends(get_db)):
    return OrderRepository(db)

@app.post("/orders")
def create_order(order: OrderCreate, repo: OrderRepository = Depends(get_orders_repository)):
    try:
        return services.create_order(repo, order.item)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order item")

@app.get("/orders/{order_id}")
def get_order(order_id: int, repo: OrderRepository = Depends(get_orders_repository)):
    try:
        return services.get_order(repo, order_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/orders")
def list_orders(repo: OrderRepository = Depends(get_orders_repository)):
    try:
        return services.list_orders(repo)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.put("/orders/{order_id}")
def update_order(order_id: int, payload: OrderUpdate, repo: OrderRepository = Depends(get_orders_repository)):
    try:
        updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
        return services.update_order(repo, order_id, **updates)
    except ValueError:
        raise HTTPException(status_code=404, detail="Order not found")
    except InvalidOrderTransition as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/orders/{order_id}")
def delete_order(order_id: int, repo: OrderRepository = Depends(get_orders_repository)):
    try:
        return services.delete_order(repo, order_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Order not found")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "use_s3": "USE_S3",
        "bedrock_model": "BEDROCK_MODEL_ID"
    }



@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())

        # Load conversation history
        conversation = load_conversation(session_id)

        # Build messages for OpenAI
        messages = [{"role": "system", "content": "You are a helpful customer support assistant."}]

        # Add conversation history (keep last 10 messages for context window)
        for msg in conversation[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Add current user message
        messages.append({"role": "user", "content": request.message})

        # Call OpenAI API
        response = await agent_chat(messages)
        assistant_response = response.final_output
        print(f"Assistant response: {assistant_response}")

        # Update conversation history
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

        # Save conversation
        save_conversation(session_id, conversation)

        return ChatResponse(response=assistant_response, session_id=session_id)

    except Exception as e:
        print(f"Exception: {e}")
        print(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/conversation/{session_id}")
async def get_conversation(session_id: str):
    """Retrieve conversation history"""
    try:
        conversation = load_conversation(session_id)
        return {"session_id": session_id, "messages": conversation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
