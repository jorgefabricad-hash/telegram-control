import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
EXPORTS_DIR = BASE_DIR / "reports" / "exports"

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID", "0"))
_extra = os.getenv("ALLOWED_USER_IDS", "")
ALLOWED_USER_IDS: set[int] = {ALLOWED_USER_ID} | {int(x) for x in _extra.split(",") if x.strip().isdigit()}
API_PORT = int(os.getenv("API_PORT", "10000"))

BLOCKED_COMMANDS = [
    "rm", "del", "format", "mkfs", "dd", "shutdown", "reboot",
    "rmdir", "deltree", "fdisk", "diskpart", ":(){:|:&};:",
]
