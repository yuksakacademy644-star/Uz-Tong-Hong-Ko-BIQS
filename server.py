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

_bot_application = None

async def keep_awake_loop(target_url: str):
    import asyncio
    import httpx
    print(f"[KEEP-AWAKE] 🚀 Self-ping background task active for {target_url}")
    await asyncio.sleep(30)
    while True:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(f"{target_url}/health")
                print(f"[KEEP-AWAKE] ⏰ Self-ping sent to {target_url}/health -> status {res.status_code}")
        except Exception as e:
            print(f"[KEEP-AWAKE] Ping error: {e}")
        await asyncio.sleep(600)  # Ping every 10 minutes (600s)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan:
    - Render (production) → webhook mode: bot lives inside FastAPI, instant response + keep-awake self-ping
    - Local → polling mode: bot runs separately in run.py, lifespan does nothing
    """
    global _bot_application
    database.init_db()

    render_url = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")
    if not render_url and getattr(config, "PRODUCTION_URL", ""):
        render_url = config.PRODUCTION_URL.rstrip("/")

    is_render = bool(os.environ.get("RENDER")) or bool(os.environ.get("RENDER_SERVICE_ID"))

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

        # Launch 24/7 background keep-awake self-ping so Render free tier NEVER sleeps
        import asyncio
        asyncio.create_task(keep_awake_loop(render_url))
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
    master_name: Optional[str] = "Руководство"
    created_by: int
    target_role: Optional[str] = "worker"

class AddAdminRequest(BaseModel):
    identifier: str
    permissions: list[str] = ["create_codes", "view_workers", "broadcast"]
    added_by: int


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
    is_admin = database.is_admin_or_superadmin(telegram_id)
    if not user:
        return {"error": "not_registered", "is_admin": is_admin}
    user["is_admin"] = is_admin
    if "role" not in user or not user["role"]:
        user["role"] = "superadmin" if is_admin else "worker"
    return user

# My Team (Master / Chief Shop Monitoring)
@app.get("/api/my_team")
async def get_my_team_route(telegram_id: int = Query(...)):
    user = database.get_user(telegram_id)
    is_admin = database.is_admin_or_superadmin(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    role = user.get("role", "worker")
    allowed_team_roles = {'nachalnik', 'master', 'brigadir', 'brigadier', 'quality', 'director', 'engineer', 'admin', 'superadmin'}
    if role not in allowed_team_roles and not is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    workers = database.get_subordinates(telegram_id)
    
    # Restrict detailed mistake logs for master and brigadir (only higher management can see detailed mistakes)
    if role in ('master', 'brigadir', 'brigadier'):
        for w in workers:
            w['latest_mistakes'] = None

    shop_name = user.get("shop_name", "СП Уз Тонг Хонг Ко")
    return {
        "shop_name": shop_name,
        "workers": workers
    }

# BIQS Elements
@app.get("/api/elements")
async def get_elements():
    return database.get_biqs_elements()

# Quiz (random 10 questions with randomized option orders)
@app.get("/api/quiz")
async def get_quiz(telegram_id: Optional[int] = Query(None)):
    if telegram_id:
        can_take, remaining = database.check_user_cooldown(telegram_id)
        if not can_take:
            mins = remaining // 60
            secs = remaining % 60
            time_str = f"{mins} min {secs} sec" if mins > 0 else f"{secs} sec"
            raise HTTPException(
                status_code=429,
                detail=f"Cooldown active. Please wait {time_str} before retrying."
            )
    questions = database.get_biqs_questions()
    random.shuffle(questions)
    selected = questions[:10]

    # Dynamically shuffle option positions for each question
    shuffled_questions = []
    for q in selected:
        q_copy = dict(q)
        opts_uz = list(q["options_uz"])
        opts_ru = list(q["options_ru"])
        orig_correct = q["correct"]

        # Zip options with index to keep uz and ru aligned
        combined = list(zip(opts_uz, opts_ru, range(len(opts_uz))))
        random.shuffle(combined)

        new_opts_uz = [c[0] for c in combined]
        new_opts_ru = [c[1] for c in combined]
        new_correct = next(i for i, c in enumerate(combined) if c[2] == orig_correct)

        q_copy["options_uz"] = new_opts_uz
        q_copy["options_ru"] = new_opts_ru
        q_copy["correct"] = new_correct
        shuffled_questions.append(q_copy)

    return shuffled_questions

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

# Leaderboard & Sector Statistics
@app.get("/api/leaderboard")
async def get_leaderboard_route(user_telegram_id: Optional[int] = None, shop_name: Optional[str] = None):
    # Check permissions
    allowed_roles = {'superadmin', 'admin', 'director', 'quality', 'engineer', 'nachalnik'}
    role = 'worker'
    if user_telegram_id:
        user = database.get_user(user_telegram_id)
        if user:
            role = user.get("role", "worker")
            # If the user is admin/superadmin in config, override
            is_admin = database.is_admin_or_superadmin(user_telegram_id)
            if is_admin:
                role = "superadmin"

    if role in allowed_roles:
        leaders = database.get_leaderboard(limit=500, shop_name=shop_name)
        sector_stats = database.get_shop_statistics()
    else:
        leaders = []
        sector_stats = []

    my_stats = {"tests_count": 0, "best_score": 0, "avg_score": 0}
    if user_telegram_id:
        my_stats = database.get_user_stats(user_telegram_id)
    return {
        "leaderboard": leaders, 
        "sector_stats": sector_stats,
        "my_stats": my_stats
    }

@app.get("/api/sector_stats")
async def get_sector_stats_route(user_telegram_id: Optional[int] = None):
    allowed_roles = {'superadmin', 'admin', 'director', 'quality', 'engineer', 'nachalnik'}
    role = 'worker'
    if user_telegram_id:
        user = database.get_user(user_telegram_id)
        if user:
            role = user.get("role", "worker")
            is_admin = database.is_admin_or_superadmin(user_telegram_id)
            if is_admin:
                role = "superadmin"
                
    if role in allowed_roles:
        return database.get_shop_statistics()
    else:
        return []


# ─────────────────────────────────────────────
# Monthly Reports & Historical Archives API
# ─────────────────────────────────────────────
REPORT_ALLOWED_ROLES = {'superadmin', 'admin', 'director', 'quality', 'engineer', 'nachalnik'}

@app.get("/api/reports/months")
async def get_report_months_route(telegram_id: int = Query(...)):
    user = database.get_user(telegram_id)
    is_admin = database.is_admin_or_superadmin(telegram_id)
    role = user.get("role", "worker") if user else "worker"
    if role not in REPORT_ALLOWED_ROLES and not is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    return database.get_available_report_months()

@app.get("/api/reports/monthly")
async def get_monthly_report_route(telegram_id: int = Query(...), month: str = Query("current")):
    user = database.get_user(telegram_id)
    is_admin = database.is_admin_or_superadmin(telegram_id)
    role = user.get("role", "worker") if user else "worker"
    if role not in REPORT_ALLOWED_ROLES and not is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    return database.get_monthly_test_results(month_code=month)

@app.get("/api/reports/export")
async def export_report_file_route(telegram_id: int = Query(...), month: str = Query("current"), format: str = Query("xlsx")):
    user = database.get_user(telegram_id)
    is_admin = database.is_admin_or_superadmin(telegram_id)
    role = user.get("role", "worker") if user else "worker"
    if role not in REPORT_ALLOWED_ROLES and not is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    filepath = database.generate_monthly_report_file(month_code=month, file_format=format)
    filename = os.path.basename(filepath)
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == "xlsx" else "text/csv"
    return FileResponse(filepath, media_type=media_type, filename=filename)



# Admin API
@app.get("/api/admin/codes")
async def get_admin_codes():
    return database.get_all_invite_codes()

@app.get("/api/admin/workers")
async def get_admin_workers():
    return database.get_all_workers_admin()

@app.get("/api/admin/admins")
async def get_admins_route(telegram_id: int = Query(...)):
    if not database.check_user_permission(telegram_id, "manage_admins"):
        raise HTTPException(status_code=403, detail="Access denied")
    return database.get_all_admins()

@app.post("/api/admin/add_admin")
async def add_admin_route(data: AddAdminRequest):
    if not database.check_user_permission(data.added_by, "manage_admins"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    target_user = database.get_user_by_username_or_id(data.identifier)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    database.set_user_role_and_permissions(target_user["telegram_id"], "admin", data.permissions)
    return {"status": "success", "user": target_user["full_name"], "permissions": data.permissions}

@app.get("/api/admin/attacks")
async def get_attacks_route(telegram_id: int = Query(...)):
    if not database.check_user_permission(telegram_id, "view_attacks"):
        raise HTTPException(status_code=403, detail="Access denied")
    return database.get_attacks_summary()

@app.post("/api/admin/create_code")
async def create_admin_code(data: CreateCodeRequest):
    database.add_invite_code(
        code=data.code,
        shop_name=data.shop_name,
        master_name=data.master_name or "Руководство",
        created_by=data.created_by,
        target_role=data.target_role or "worker"
    )
    return {"status": "created", "code": data.code, "target_role": data.target_role}

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
