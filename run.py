import sys
import os
import threading
import time
import subprocess
import re
import uvicorn

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import config
import database
from server import app as fastapi_app
from bot import create_bot_app, set_webapp_url

import requests

def start_fastapi():
    print("[SERVER] Starting FastAPI Server on http://0.0.0.0:8000 ...")
    uvicorn.run(fastapi_app, host=config.HOST, port=config.PORT, log_level="info")

def keep_awake_bg():
    if not os.environ.get("RENDER"):
        return
    render_url = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")
    if not render_url:
        return
    health_url = render_url + "/health"
    print(f"[KEEP-AWAKE] 🟢 Started pinging {health_url} every 4 minutes to prevent sleep...")
    while True:
        time.sleep(240)  # 4 minutes (Render sleeps after 15 min inactivity)
        try:
            r = requests.get(health_url, timeout=10)
            print(f"[KEEP-AWAKE] ✅ Ping OK: {r.status_code}")
        except Exception as e:
            print(f"[KEEP-AWAKE] ⚠️ Ping failed: {e}")

def setup_tunnel_bg():
    custom_url = os.environ.get("WEBAPP_URL")

    if os.environ.get("RENDER"):
        render_url = os.environ.get("RENDER_EXTERNAL_URL")
        print(f"[TUNNEL] Running on Render. Setting WEBAPP_URL to: {render_url}")
        set_webapp_url(render_url)
        return

    if custom_url:
        print(f"[TUNNEL] Using custom WEBAPP_URL: {custom_url}")
        set_webapp_url(custom_url)
        return

    # ✅ Локальный запуск — используем постоянный Render URL (никаких туннелей!)
    # Это исключает Pinggy, localhost.run и любые страницы предупреждений навсегда.
    production_url = getattr(config, "PRODUCTION_URL", "")
    if production_url:
        print(f"[TUNNEL] 🌐 Local mode → using Production URL: {production_url}")
        set_webapp_url(production_url)
        return

    # Attempt 1: ngrok (if authtoken is present)
    ngrok_authtoken = getattr(config, "NGROK_AUTHTOKEN", "") or os.environ.get("NGROK_AUTHTOKEN")
    if ngrok_authtoken and len(ngrok_authtoken.strip()) > 5:
        try:
            from pyngrok import ngrok
            ngrok.set_auth_token(ngrok_authtoken.strip())
            tunnel = ngrok.connect(config.PORT, "http")
            public_url = tunnel.public_url.replace("http://", "https://")
            print(f"\n=======================================================")
            print(f"🚀 PUBLIC WEBAPP HTTPS URL (NGROK PRO): {public_url}")
            print(f"=======================================================\n")
            set_webapp_url(public_url)
            return
        except Exception as e:
            print(f"[TUNNEL NGROK ERROR] {e}")

    # Tunnel Monitor & Reconnect Loop
    while True:
        # Attempt 2: Cloudflared FIRST ✅ (no warning page, exe already in project)
        cloudflared_bin = "cloudflared.exe" if os.path.exists("cloudflared.exe") else "cloudflared"
        try:
            print("[TUNNEL] 🌩️ Attempting Cloudflare Tunnel (no warning page)...")
            cmd = [cloudflared_bin, "tunnel", "--url", f"http://127.0.0.1:{config.PORT}"]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

            tunnel_established = False
            for line in proc.stdout:
                line_str = line.strip()
                print(f"[CLOUDFLARED LOG] {line_str}")
                match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line_str)
                if match:
                    base_url = match.group(0)
                    print(f"\n=======================================================")
                    print(f"🚀 PUBLIC WEBAPP HTTPS URL (CLOUDFLARE): {base_url}")
                    print(f"=======================================================\n")
                    set_webapp_url(base_url)
                    tunnel_established = True

            if tunnel_established and proc.poll() is None:
                proc.wait()
        except Exception as e:
            print(f"[CLOUDFLARE ERROR] {e}")

        # Attempt 3: Localhost.run (fallback, also no warning page)
        try:
            print("[TUNNEL] Initiating Localhost.run HTTPS tunnel fallback...")
            cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ServerAliveInterval=15", "-R", f"80:127.0.0.1:{config.PORT}", "nokey@localhost.run"]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

            tunnel_established = False
            for line in proc.stdout:
                line_str = line.strip()
                print(f"[LOCALHOST.RUN LOG] {line_str}")
                match = re.search(r'https://[a-zA-Z0-9-]+\.(lhr\.life|lh\.life)', line_str)
                if match:
                    base_url = match.group(0)
                    print(f"\n=======================================================")
                    print(f"🚀 PUBLIC WEBAPP HTTPS URL (LOCALHOST.RUN): {base_url}")
                    print(f"=======================================================\n")
                    set_webapp_url(base_url)
                    tunnel_established = True

            if tunnel_established and proc.poll() is None:
                proc.wait()
        except Exception as e:
            print(f"[LOCALHOST.RUN ERROR] {e}")

        print("[TUNNEL RETRY] Tunnel connection closed. Re-establishing in 3 seconds...")
        time.sleep(3)



def main():
    print("[INIT] Initializing Uz Tong Hong Ko BIQS Database...")
    database.init_db()

    # Start Keep Awake (only active on Render)
    keep_awake_thread = threading.Thread(target=keep_awake_bg, daemon=True)
    keep_awake_thread.start()

    # ── PRODUCTION (Render): Webhook mode ────────────────────────────────────
    # Bot is initialized inside FastAPI lifespan (server.py).
    # Telegram pushes updates to /webhook → instant response, no cold-start delay.
    if os.environ.get("RENDER"):
        print("[RUN] 🚀 Production mode: FastAPI + Webhook Bot starting...")
        uvicorn.run(fastapi_app, host=config.HOST, port=config.PORT, log_level="info")
        return

    # ── LOCAL: Polling mode / Render Webhook Detection ──────────────────────
    print("[RUN] 🖥️  Local mode: Starting local FastAPI server...")

    server_thread = threading.Thread(target=start_fastapi, daemon=True)
    server_thread.start()

    tunnel_thread = threading.Thread(target=setup_tunnel_bg, daemon=True)
    tunnel_thread.start()

    time.sleep(2)

    # Check if Render Webhook bot is already online
    prod_url = getattr(config, "PRODUCTION_URL", "").rstrip("/")
    render_webhook_online = False
    if prod_url:
        try:
            r = requests.get(f"{prod_url}/health", timeout=4)
            if r.status_code == 200 and r.json().get("mode") == "webhook":
                render_webhook_online = True
        except Exception:
            render_webhook_online = False

    if render_webhook_online:
        print("\n==================================================================")
        print("🟢 PRODUCTION BOT IS ACTIVE 24/7 ON RENDER (WEBHOOK MODE)!")
        print("⚡ All Telegram messages are handled instantly by Render.")
        print("🛡️ Local polling SKIPPED to preserve Render Webhook 24/7 uptime.")
        print("==================================================================\n")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            print("[SHUTDOWN] Exiting...")
            return

    print("[BOT] Render Webhook offline or not configured. Starting local polling...")
    from telegram import Update
    while True:
        try:
            bot_app = create_bot_app(webhook_mode=False)
            bot_app.run_polling(
                drop_pending_updates=False,
                poll_interval=1.0,
                allowed_updates=Update.ALL_TYPES
            )
            break
        except Exception as err:
            print(f"[BOT RETRY] Connection warning: {err}. Retrying in 3s...")
            time.sleep(3)

if __name__ == "__main__":
    main()
