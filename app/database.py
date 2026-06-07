from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client = AsyncIOMotorClient(settings.MONGODB_URI)

# Extract database name from URI or use a default
# E.g. mongodb+srv://.../exam-flow?retryWrites=true
# Mongoose connects to "exam-flow" database from the URI
db_name = "exam-flow"
if "?" in settings.MONGODB_URI.split("/")[-1]:
    db_name = settings.MONGODB_URI.split("/")[-1].split("?")[0]
else:
    db_name = settings.MONGODB_URI.split("/")[-1] or "exam-flow"

db = client[db_name]

# Helper collections
parents_collection = db["parents"]
hospitals_collection = db["hospitals"]
children_collection = db["children"]
appointments_collection = db["appointments"]

async def check_db_connection():
    try:
        # The ismaster command is cheap and does not require auth.
        await db.command("ping")
        print("[SUCCESS] MongoDB Connected Successfully (Python)")
        return True
    except Exception as e:
        print(f"[ERROR] MongoDB Connection Error (Python): {e}")
        return False
