import os

bot_env = os.environ.get("BOT_TOKEN")
BOT_TOKEN = bot_env if bot_env and bot_env.strip() else "8876317770:AAGVtad4BXnD3oNqTNr-jVoMHHYBPnHgAVo"
admin_env = os.environ.get("ADMIN_IDS")
ADMIN_IDS = [int(x.strip()) for x in admin_env.split(",") if x.strip()] if admin_env and admin_env.strip() else [5543183063]
DB_PATH = os.environ.get("DB_PATH", "biqs_uztonghong.db")
PORT = int(os.environ.get("PORT", 8000))
HOST = "0.0.0.0"

db_dir = os.path.dirname(DB_PATH)
if db_dir and not os.path.exists(db_dir):
    try:
        os.makedirs(db_dir, exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create directory {db_dir} for database: {e}. Falling back to local directory.")
        DB_PATH = "biqs_uztonghong.db"

# Optional: Insert your free Ngrok Authtoken here to remove warning screens 100% permanently!
# Get token free from https://dashboard.ngrok.com/get-started/your-authtoken
NGROK_AUTHTOKEN = ""
