import os
import requests
import random
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional

from fastapi.middleware.cors import CORSMiddleware

import config
import database

app = FastAPI(title="Uz Tong Hong Ko BIQS Mini App Server")

# Enable CORS for Telegram WebApp
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom header middleware for iframe compatibility inside Telegram WebApp
@app.middleware("http")
async def add_telegram_webapp_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "ALLOWALL"
    response.headers["Content-Security-Policy"] = "frame-ancestors *;"
    return response

# Mount Static & Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize DB
database.init_db()

# Pydantic Schemas
class QuizSubmitRequest(BaseModel):
    user_telegram_id: int
    score: int
    total_questions: int
    percentage: float
    time_taken_seconds: int
    mistakes: list[str] = []

class CreateCodeRequest(BaseModel):
    code: str
    shop_name: str
    master_name: str
    created_by: int

# Helper: Send Telegram Notification to Admin
def send_admin_notification(text: str):
    try:
        url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
        for admin_id in config.ADMIN_IDS:
            requests.post(url, json={
                "chat_id": admin_id,
                "text": text,
                "parse_mode": "HTML"
            }, timeout=3)
    except Exception as e:
        print(f"Failed to send admin notification: {e}")

# WebApp Root Page
@app.get("/", response_class=HTMLResponse)
async def serve_miniapp(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


# API Routes
@app.get("/api/user_info")
async def get_user_info(telegram_id: int = Query(...)):
    user = database.get_user(telegram_id)
    is_admin = telegram_id in config.ADMIN_IDS
    if not user:
        return {"error": "not_registered", "is_admin": is_admin}
    
    user["is_admin"] = is_admin
    return user

@app.get("/api/elements")
async def get_elements():
    return database.get_biqs_elements()

@app.get("/api/quiz")
async def get_quiz():
    questions = database.get_biqs_questions()
    random.shuffle(questions)
    return questions[:10]

@app.post("/api/quiz/submit")
async def submit_quiz(data: QuizSubmitRequest):
    import json
    mistakes_str = json.dumps(data.mistakes, ensure_ascii=False) if data.mistakes else ""
    database.save_test_result(
        telegram_id=data.user_telegram_id,
        score=data.score,
        total=data.total_questions,
        percentage=data.percentage,
        time_taken=data.time_taken_seconds,
        mistakes=mistakes_str
    )

    user = database.get_user(data.user_telegram_id)
    full_name = user["full_name"] if user else f"ID: {data.user_telegram_id}"
    shop = user["shop_name"] if user else "СП Уз Тонг Хонг Ко"
    phone = user.get("phone", "Нет номера") if user else "Нет номера"

    # Result is logged in DB. Admin checks it via WebApp Admin Panel.
    return {"status": "success", "percentage": data.percentage}

@app.get("/api/leaderboard")
async def get_leaderboard_route(user_telegram_id: Optional[int] = None):
    leaders = database.get_leaderboard(20)
    my_stats = {"tests_count": 0, "best_score": 0, "avg_score": 0}
    if user_telegram_id:
        my_stats = database.get_user_stats(user_telegram_id)
    
    return {
        "leaderboard": leaders,
        "my_stats": my_stats
    }

# Admin API Routes
@app.get("/api/admin/codes")
async def get_admin_codes():
    return database.get_all_invite_codes()

@app.get("/api/admin/workers")
async def get_admin_workers():
    return database.get_all_workers_admin()

@app.post("/api/admin/create_code")
async def create_admin_code(data: CreateCodeRequest):
    database.add_invite_code(
        code=data.code,
        shop_name=data.shop_name,
        master_name=data.master_name,
        created_by=data.created_by
    )
    return {"status": "created", "code": data.code}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host=config.HOST, port=config.PORT, reload=True)
