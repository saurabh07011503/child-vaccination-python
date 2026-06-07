import uvicorn
from app.config import settings

if __name__ == "__main__":
    print(f"Starting server on port {settings.PORT}...")
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=settings.PORT, 
        reload=True if settings.ENV == "development" else False
    )
