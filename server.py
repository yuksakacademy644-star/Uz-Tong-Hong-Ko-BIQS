import os
import requests
import random
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update

import config
import database

# ─────────────────────────────────────────────
# Bot app reference (only used in webhook mode)
# ─────────────────────────────────────────────
_bot_application = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan:
    - Render (production) → webhook mode: bot lives inside FastAPI, instant response
    - Local → polling mode: bot runs separately in run.py, lifespan does nothing
    """
    global _bot_application
    database.init_db()

    render_url = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")
    if not render_url and getattr(config, "PRODUCTION_URL", ""):
        render_url = config.PRODUCTION_URL.rstrip("/")

    is_render  = bool(os.environ.get("RENDER")) or bool(os.environ.get("RENDER_SERVICE_ID"))

    if (is_render or render_url) and render_url.startswith("https://"):
        # ── PRODUCTION: Webhook mode ──────────────────────────────────────────
        from bot import create_bot_app, set_webapp_url
        set_webapp_url(render_url)                  # update WebApp URL

        _bot_application = create_bot_app(webhook_mode=True)
        await _bot_application.initialize()
        await _bot_application.start()

        webhook_url = render_url + "/webhook"
        try:
            res = await _bot_application.bot.set_webhook(
                url=webhook_url,
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=False,
            )
            print(f"[BOT] ⚡ Webhook mode ACTIVE → {webhook_url} (result: {res})")
        except Exception as e:
            print(f"[BOT ERROR] Failed to set webhook to {webhook_url}: {e}")
    else:
        # ── LOCAL: Polling mode (bot started by run.py) ───────────────────────
        print("[BOT] Local mode — polling handled by run.py")

    yield   # ← server is running

    # Shutdown
    if _bot_application:
        try:
            await _bot_application.stop()
            await _bot_application.shutdown()
            print("[BOT] Bot shutdown complete.")
        except Exception as e:
            print(f"[BOT SHUTDOWN] {e}")


# ─────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────
app = FastAPI(title="Uz Tong Hong Ko BIQS Mini App Server", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Telegram WebApp iframe headers
@app.middleware("http")
async def add_telegram_webapp_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "ALLOWALL"
    response.headers["Content-Security-Policy"] = "frame-ancestors *;"
    return response

# Static & Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ─────────────────────────────────────────────
# Pydantic Schemas
# ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

# ⚡ Telegram Webhook Endpoint (production only)
@app.post("/webhook")
async def telegram_webhook(request: Request):
    if _bot_application is None:
        return JSONResponse({"error": "bot not initialized"}, status_code=503)
    try:
        data = await request.json()
        update = Update.de_json(data, _bot_application.bot)
        await _bot_application.process_update(update)
    except Exception as e:
        print(f"[WEBHOOK ERROR] {e}")
    return {"ok": True}

# Health Check (for UptimeRobot)
@app.get("/health")
async def health_check():
    mode = "webhook" if _bot_application else "polling"
    return {"status": "ok", "service": "Uz Tong Hong Ko BIQS Bot", "mode": mode, "alive": True}

# WebApp Root Page
@app.get("/")
async def serve_miniapp():
    return FileResponse("templates/index.html")

# User Info
@app.get("/api/user_info")
async def get_user_info(telegram_id: int = Query(...)):
    user = database.get_user(telegram_id)
    is_admin = telegram_id in config.ADMIN_IDS
    if not user:
        return {"error": "not_registered", "is_admin": is_admin}
    user["is_admin"] = is_admin
    return user

# BIQS Elements
@app.get("/api/elements")
async def get_elements():
    return database.get_biqs_elements()

# Quiz (random 10 questions)
@app.get("/api/quiz")
async def get_quiz():
    questions = database.get_biqs_questions()
    random.shuffle(questions)
    return questions[:10]

# Quiz Submit
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
    return {"status": "success", "percentage": data.percentage}

# Leaderboard
@app.get("/api/leaderboard")
async def get_leaderboard_route(user_telegram_id: Optional[int] = None):
    leaders = database.get_leaderboard(20)
    my_stats = {"tests_count": 0, "best_score": 0, "avg_score": 0}
    if user_telegram_id:
        my_stats = database.get_user_stats(user_telegram_id)
    return {"leaderboard": leaders, "my_stats": my_stats}

# Admin API
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

@app.get("/api/admin/force_update_keyboards")
async def force_update_keyboards_route():
    if _bot_application is None:
        return {"error": "bot application not ready"}
    from bot import get_main_keyboard, update_chat_menu_button, WEBAPP_URL
    import asyncio
    
    # 1. Update Global Chat Menu Button
    await update_chat_menu_button(_bot_application.bot, WEBAPP_URL)
    
    # 2. Update Reply Keyboards for all workers
    workers = database.get_all_workers_admin()
    updated = 0
    for w in workers:
        try:
            lang = w.get("language", "ru")
            await _bot_application.bot.send_message(
                chat_id=w["telegram_id"],
                text="🔄 <b>Меню бота обновлено на официальную версию.</b>\n<i>Menyu rasmiy versiyaga yangilandi.</i>",
                parse_mode="HTML",
                reply_markup=get_main_keyboard(lang)
            )
            updated += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            print(f"[KB UPDATE ERR] {w.get('telegram_id')}: {e}")
            
    return {"status": "ok", "updated_users": updated, "url": WEBAPP_URL}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host=config.HOST, port=config.PORT, reload=True)
