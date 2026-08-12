import os

BOT_TOKEN = "8876317770:AAGVtad4BXnD3oNqTNr-jVoMHHYBPnHgAVo"
ADMIN_IDS = [5543183063]
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
