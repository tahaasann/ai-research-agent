from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import os

# 1. MİMARİ BAĞLANTI: Motorumuzu (main.py'daki app objesini) sunucuya dahil et
from main import app as agent_app

# Loglama ayarları
logging.basicConfig(level=logging.INFO)

# FastAPI uygulaması
app = FastAPI(title="AI Research Agent API", version="1.0.0")

# --- CORS BLOĞU ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],  # GET, POST, PUT hepsine izin ver
    allow_headers=["*"],
)


# 2. VERİ MODELİ (pydantic): Frontend'in bize göndereceği JSON formatını (Sözleşmeyi) belirliyoruz
class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default_user_1"
    api_key: str = ""  # Opsiyonel (None) olmasını kaldırdık, varsayılan boş string


@app.get("/")
async def root():
    return {"message": "AI Agent Backend Sistemine Hoş Geldiniz!"}


# 3. Endpoint: POST isteği alıp ajana ileten fonksiyon
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # YENİ: .env kontrolünü sildik! Sadece kullanıcının gönderdiği key'e bakıyoruz.
    if not request.api_key or request.api_key.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="İşlem yapabilmek için lütfen geçerli bir OpenAI API Anahtarı girin.",
        )

    try:
        # LangGraph için state'i ve config'i (hafıza kimliğini) hazırlıyoruz
        state_input = {"messages": [{"role": "user", "content": request.message}]}
        config = {
            "configurable": {"thread_id": request.thread_id, "api_key": request.api_key}
        }

        # Ajanı çalıştır (invoke)
        final_state = agent_app.invoke(state_input, config=config)

        # Sonucu çıkar
        ai_response = final_state["messages"][-1].content

        # Frontend'e sadece temiz cevabı ve hangi kullanıcının işlem yaptığını dön
        return {"response": ai_response, "thread_id": request.thread_id}

    except Exception as e:
        logging.error(f"API Hatası: {e}")
        # Uygulamanın çökmesini engelle, kullanıcıya HTTP 500 dön
        raise HTTPException(status_code=500, detail=str(e))
