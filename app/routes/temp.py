from fastapi import APIRouter, HTTPException
from app.database import hospitals_collection

router = APIRouter(prefix="/temp", tags=["Temp Utilities"])

@router.get("/verify-all-hospitals")
async def verify_all_hospitals():
    try:
        result = await hospitals_collection.update_many(
            {},
            {"$set": {"isVerified": True}}
        )

        return {
            "success": True,
            "message": f"{result.modified_count} hospitals verified successfully",
            "data": {
                "matchedCount": result.matched_count,
                "modifiedCount": result.modified_count
            }
        }
    except Exception as e:
        print(f"Auto-verify hospitals error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )
