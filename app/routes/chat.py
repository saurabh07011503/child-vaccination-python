from fastapi import APIRouter, Depends, HTTPException, status
import google.generativeai as genai
from app.models import ChatMessage
from app.config import settings
from app.auth import get_current_user

router = APIRouter(prefix="/chat", tags=["Chatbot"])

@router.post("")
async def send_message(data: ChatMessage, current_user: dict = Depends(get_current_user)):
    message = data.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    # Check if API key exists
    if not settings.GEMINI_API_KEY:
        return {
            "success": True,
            "data": "Hello! I am your Vaccine Tracker Assistant. Unfortunately, my AI brain is currently asleep because the GEMINI_API_KEY is not set in the server's .env file. Please ask the developer to configure it so I can answer your questions about child vaccinations and health!"
        }

    try:
        # Initialize Gemini API
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Use gemini-2.5-flash as configured in Node.js
        model = genai.GenerativeModel("gemini-2.5-flash")

        system_prompt = (
            "You are a helpful, empathetic, and knowledgeable pediatric assistant for the \"Vaccine Tracker\" application.\n"
            "Your goal is to help parents understand child vaccinations, appointment scheduling, and general child health.\n"
            "- Be concise, clear, and reassuring.\n"
            "- Always advise parents to consult with their actual doctor for critical medical emergencies.\n"
            "- Format your responses with bullet points if explaining a list.\n"
            "- Do not use markdown that is too complex, stick to basic text formatting, bullet points, and newlines."
        )

        # Build history structure expected by Google Generative AI Python SDK
        history_list = [
            {
                "role": "user",
                "parts": [system_prompt]
            },
            {
                "role": "model",
                "parts": ["Understood. I will act as the Vaccine Tracker pediatric assistant."]
            }
        ]

        # Map history passed from React Native app
        for msg in data.history:
            role = "model" if msg.get("isBot") else "user"
            text_val = msg.get("text", "")
            if text_val:
                history_list.append({
                    "role": role,
                    "parts": [text_val]
                })

        # Start chat session and send message
        chat = model.start_chat(history=history_list)
        
        # Generation configuration
        config = genai.types.GenerationConfig(
            max_output_tokens=500,
            temperature=0.7
        )
        
        # Note: send_message is a synchronous call in standard genai client,
        # but running in a FastAPI async endpoint is fine. To avoid blocking the event loop,
        # we can run it in a thread pool using anyio or run_in_executor if needed,
        # but for simplicity/direct match, standard call is acceptable.
        response = chat.send_message(message, generation_config=config)
        response_text = response.text

        return {
            "success": True,
            "data": response_text
        }

    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat message: {str(e)}"
        )
