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

def start_fastapi():
    print("[SERVER] Starting FastAPI Server on http://0.0.0.0:8000 ...")
    uvicorn.run(fastapi_app, host=config.HOST, port=config.PORT, log_level="info")

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
        # Attempt 2: Localhost.run SSH Tunnel (High reliability, explicit 127.0.0.1 IPv4 forwarding)
        try:
            print("[TUNNEL] Initiating Localhost.run HTTPS tunnel...")
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

        # Attempt 3: Pinggy Fallback (127.0.0.1 IPv4)
        try:
            print("[TUNNEL] Initiating Pinggy HTTPS tunnel fallback...")
            cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-p", "443", "-R", f"0:127.0.0.1:{config.PORT}", "qr@a.pinggy.io"]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

            for line in proc.stdout:
                line_str = line.strip()
                print(f"[PINGGY LOG] {line_str}")
                match = re.search(r'https://[a-zA-Z0-9-]+\.(free\.pinggy\.net|run\.pinggy-free\.link)', line_str)
                if match:
                    base_url = match.group(0)
                    print(f"\n=======================================================")
                    print(f"🚀 PUBLIC WEBAPP HTTPS URL (PINGGY): {base_url}")
                    print(f"=======================================================\n")
                    set_webapp_url(base_url)
                    break
            if proc.poll() is None:
                proc.wait()
        except Exception as e:
            print(f"[PINGGY ERROR] {e}")

        # Attempt 4: Cloudflared (if local exe exists)
        cloudflared_bin = "cloudflared.exe" if os.path.exists("cloudflared.exe") else "cloudflared"
        try:
            print("[TUNNEL] Attempting Cloudflare Tunnel...")
            cmd = [cloudflared_bin, "tunnel", "--url", f"http://127.0.0.1:{config.PORT}"]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

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
                    break
            if proc.poll() is None:
                proc.wait()
        except Exception as e:
            print(f"[CLOUDFLARE ERROR] {e}")

        print("[TUNNEL RETRY] Tunnel connection closed. Re-establishing in 3 seconds...")
        time.sleep(3)



def main():
    print("[INIT] Initializing Uz Tong Hong Ko BIQS Database...")
    database.init_db()

    # Start FastAPI
    server_thread = threading.Thread(target=start_fastapi, daemon=True)
    server_thread.start()

    # Start Tunnel
    tunnel_thread = threading.Thread(target=setup_tunnel_bg, daemon=True)
    tunnel_thread.start()

    time.sleep(2)

    # Start Bot
    print("[BOT] Starting Telegram Bot Polling (@UzTongHong_BIQS_bot)...")
    while True:
        try:
            bot_app = create_bot_app()
            bot_app.run_polling(drop_pending_updates=True, poll_interval=1.0)
            break
        except Exception as err:
            print(f"[BOT RETRY] Connection warning: {err}. Retrying in 3s...")
            time.sleep(3)

if __name__ == "__main__":
    main()
