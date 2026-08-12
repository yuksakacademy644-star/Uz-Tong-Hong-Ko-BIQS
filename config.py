import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8876317770:AAGVtad4BXnD3oNqTNr-jVoMHHYBPnHgAVo")
admin_env = os.environ.get("ADMIN_IDS")
ADMIN_IDS = [int(x.strip()) for x in admin_env.split(",")] if admin_env else [5543183063]
DB_PATH = os.environ.get("DB_PATH", "biqs_uztonghong.db")
PORT = int(os.environ.get("PORT", 8000))
HOST = "0.0.0.0"

# Optional: Insert your free Ngrok Authtoken here to remove warning screens 100% permanently!
# Get token free from https://dashboard.ngrok.com/get-started/your-authtoken
NGROK_AUTHTOKEN = ""
