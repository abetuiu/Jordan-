from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import uuid
from datetime import datetime
import json
from pymongo import MongoClient
from bson import ObjectId
import asyncio

# Import emergentintegrations (will be installed)
try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    from emergentintegrations.llm.openai import OpenAIChatRealtime
    INTEGRATIONS_AVAILABLE = True
except ImportError:
    INTEGRATIONS_AVAILABLE = False
    print("Warning: emergentintegrations not available. Using mock responses.")

# Initialize FastAPI
app = FastAPI(title="Multi-Personality AI Chatbot", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URL)
db = client.ai_chatbot

# Collections
personalities_collection = db.personalities
conversations_collection = db.conversations
messages_collection = db.messages

# Pydantic models
class PersonalityCreate(BaseModel):
    name: str
    description: str
    system_prompt: str
    avatar_color: str
    personality_traits: List[str]

class MessageCreate(BaseModel):
    text: str
    personality_id: str
    session_id: Optional[str] = None

class VoiceMessageCreate(BaseModel):
    audio_data: str  # Base64 encoded audio
    personality_id: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    personality_id: str
    session_id: str
    timestamp: datetime
    message_id: str

# Initialize OpenAI integration if available
openai_api_key = os.environ.get('OPENAI_API_KEY', '')
realtime_chat = None
if INTEGRATIONS_AVAILABLE and openai_api_key:
    realtime_chat = OpenAIChatRealtime(api_key=openai_api_key)

# Default AI Personalities
DEFAULT_PERSONALITIES = [
    {
        "_id": "assistant",
        "name": "Assistant",
        "description": "Helpful and professional AI assistant",
        "system_prompt": "You are a helpful, professional AI assistant. Provide clear, accurate, and detailed responses. Be supportive and informative.",
        "avatar_color": "blue",
        "personality_traits": ["Professional", "Helpful", "Clear", "Detailed"]
    },
    {
        "_id": "creative",
        "name": "Creative",
        "description": "Artistic and imaginative AI companion",
        "system_prompt": "You are a creative, artistic, and imaginative AI. Think outside the box, be inspiring, and bring a unique perspective to every conversation. Use metaphors and creative language.",
        "avatar_color": "purple",
        "personality_traits": ["Artistic", "Imaginative", "Inspiring", "Unique"]
    },
    {
        "_id": "expert",
        "name": "Expert",
        "description": "Technical and analytical AI specialist",
        "system_prompt": "You are a technical expert and analytical thinker. Provide in-depth, precise, and well-researched responses. Focus on facts, data, and logical reasoning.",
        "avatar_color": "green",
        "personality_traits": ["Technical", "Analytical", "Precise", "Logical"]
    },
    {
        "_id": "friend",
        "name": "Friend",
        "description": "Casual and supportive AI companion",
        "system_prompt": "You are a friendly, casual, and supportive companion. Be warm, empathetic, and conversational. Use a relaxed tone and show genuine interest in the user.",
        "avatar_color": "orange",
        "personality_traits": ["Friendly", "Casual", "Supportive", "Warm"]
    }
]

# Initialize personalities in database
@app.on_event("startup")
async def startup_event():
    # Create default personalities if they don't exist
    for personality in DEFAULT_PERSONALITIES:
        existing = personalities_collection.find_one({"_id": personality["_id"]})
        if not existing:
            personalities_collection.insert_one(personality)
    print("AI Chatbot server started successfully!")

# Mock AI response function
async def get_mock_ai_response(message: str, personality: Dict) -> str:
    """Generate mock responses based on personality"""
    responses = {
        "assistant": f"As your AI assistant, I understand you're asking about: '{message}'. Let me provide you with a helpful and detailed response. This is a professional analysis of your query.",
        "creative": f"What an inspiring question about '{message}'! 🎨 Let me paint you a picture with words... This reminds me of a canvas waiting to be filled with possibilities.",
        "expert": f"From a technical perspective regarding '{message}': This requires analytical consideration. Based on current data and research, here's a comprehensive analysis.",
        "friend": f"Hey! Great question about '{message}' 😊 You know what I think? This is actually pretty interesting to talk about. Let me share my thoughts with you..."
    }
    return responses.get(personality["_id"], "I understand your message and I'm here to help!")

# API Routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "integrations_available": INTEGRATIONS_AVAILABLE}

@app.get("/api/personalities")
async def get_personalities():
    personalities = list(personalities_collection.find({}, {"_id": 1, "name": 1, "description": 1, "avatar_color": 1, "personality_traits": 1}))
    return {"personalities": personalities}

@app.get("/api/conversations/{session_id}")
async def get_conversation(session_id: str):
    conversation = conversations_collection.find_one({"session_id": session_id})
    if not conversation:
        return {"messages": []}
    
    messages = list(messages_collection.find(
        {"session_id": session_id}
    ).sort("timestamp", 1))
    
    # Convert ObjectId to string
    for message in messages:
        message["_id"] = str(message["_id"])
    
    return {"messages": messages}

@app.post("/api/chat")
async def send_message(message_data: MessageCreate):
    try:
        # Get personality
        personality = personalities_collection.find_one({"_id": message_data.personality_id})
        if not personality:
            raise HTTPException(status_code=404, detail="Personality not found")
        
        # Generate session ID if not provided
        session_id = message_data.session_id or str(uuid.uuid4())
        
        # Store user message
        user_message = {
            "session_id": session_id,
            "personality_id": message_data.personality_id,
            "role": "user",
            "content": message_data.text,
            "timestamp": datetime.utcnow(),
            "message_type": "text"
        }
        user_message_id = messages_collection.insert_one(user_message).inserted_id
        
        # Generate AI response
        if INTEGRATIONS_AVAILABLE and openai_api_key:
            try:
                # Use real OpenAI integration
                chat = LlmChat(
                    api_key=openai_api_key,
                    session_id=session_id,
                    system_message=personality["system_prompt"]
                ).with_model("openai", "gpt-4o")
                
                user_msg = UserMessage(text=message_data.text)
                ai_response = await chat.send_message(user_msg)
                
            except Exception as e:
                print(f"OpenAI API error: {e}")
                ai_response = await get_mock_ai_response(message_data.text, personality)
        else:
            ai_response = await get_mock_ai_response(message_data.text, personality)
        
        # Store AI response
        ai_message = {
            "session_id": session_id,
            "personality_id": message_data.personality_id,
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.utcnow(),
            "message_type": "text"
        }
        ai_message_id = messages_collection.insert_one(ai_message).inserted_id
        
        # Update or create conversation
        conversations_collection.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "session_id": session_id,
                    "personality_id": message_data.personality_id,
                    "last_updated": datetime.utcnow()
                },
                "$setOnInsert": {"created_at": datetime.utcnow()}
            },
            upsert=True
        )
        
        return ChatResponse(
            message=ai_response,
            personality_id=message_data.personality_id,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            message_id=str(ai_message_id)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.post("/api/voice/send")
async def send_voice_message(voice_data: VoiceMessageCreate):
    try:
        # Get personality
        personality = personalities_collection.find_one({"_id": voice_data.personality_id})
        if not personality:
            raise HTTPException(status_code=404, detail="Personality not found")
        
        # Generate session ID if not provided
        session_id = voice_data.session_id or str(uuid.uuid4())
        
        # Store voice message (for now, we'll simulate transcription)
        user_message = {
            "session_id": session_id,
            "personality_id": voice_data.personality_id,
            "role": "user",
            "content": "[Voice message received]",
            "audio_data": voice_data.audio_data,
            "timestamp": datetime.utcnow(),
            "message_type": "voice"
        }
        messages_collection.insert_one(user_message)
        
        # Generate mock response (in real implementation, would process voice)
        mock_transcription = "I received your voice message"
        ai_response = await get_mock_ai_response(mock_transcription, personality)
        
        # Store AI response
        ai_message = {
            "session_id": session_id,
            "personality_id": voice_data.personality_id,
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.utcnow(),
            "message_type": "text"
        }
        ai_message_id = messages_collection.insert_one(ai_message).inserted_id
        
        return ChatResponse(
            message=ai_response,
            personality_id=voice_data.personality_id,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            message_id=str(ai_message_id)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing voice message: {str(e)}")

# Realtime Voice Routes (if available)
if INTEGRATIONS_AVAILABLE and realtime_chat:
    try:
        router = APIRouter()
        OpenAIChatRealtime.register_openai_realtime_router(router, realtime_chat)
        app.include_router(router, prefix="/api/realtime")
        print("Realtime voice chat routes registered!")
    except Exception as e:
        print(f"Error setting up realtime routes: {e}")

@app.get("/api/sessions/new")
async def create_new_session():
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    return {"session_id": session_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)