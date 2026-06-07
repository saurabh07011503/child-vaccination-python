from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import check_db_connection
from app.utils.scheduler import start_scheduler, scheduler
from app.routes import parent_auth, hospital_auth, child, appointment, admin, chat, temp

app = FastAPI(
    title="Child Vaccination Tracker API",
    description="Python FastAPI backend for tracking child vaccinations, booking appointments, and AI chat assistance.",
    version="1.0.0"
)

# CORS middleware to allow mobile clients and browsers to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers under /api prefix
app.include_router(parent_auth.router, prefix="/api")
app.include_router(hospital_auth.router, prefix="/api")
app.include_router(child.router, prefix="/api")
app.include_router(appointment.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(temp.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "success": True,
        "message": "Child Vaccination Tracker API (Python FastAPI) is running.",
        "docs": "/docs"
    }

@app.on_event("startup")
async def startup_event():
    # Verify DB connection on startup
    await check_db_connection()
    # Initialize and start scheduler for 10-minute reminders
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down scheduler...")
    if scheduler.running:
        scheduler.shutdown()
