from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from app.models import serialize_doc, serialize_list
from app.database import hospitals_collection
from app.auth import authorize_roles

router = APIRouter(prefix="/admin", tags=["Admin Management"])

@router.get("/hospitals")
async def get_all_hospitals(current_user: dict = Depends(authorize_roles(["admin"]))):
    cursor = hospitals_collection.find({}, {"password": 0})
    hospitals = []
    async for h in cursor:
        hospitals.append(serialize_doc(h))
    return {
        "success": True,
        "count": len(hospitals),
        "data": hospitals
    }

@router.put("/hospitals/{id}/verify")
async def verify_hospital(id: str, current_user: dict = Depends(authorize_roles(["admin"]))):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid hospital ID")

    hospital = await hospitals_collection.find_one({"_id": ObjectId(id)})
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    await hospitals_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"isVerified": True}}
    )

    return {
        "success": True,
        "message": "Hospital verified successfully",
        "data": {
            "id": str(hospital["_id"]),
            "name": hospital.get("name"),
            "email": hospital.get("email"),
            "isVerified": True
        }
    }

@router.put("/hospitals/{id}/status")
async def update_hospital_status(
    id: str,
    data: dict, # accepts {"isVerified": bool, "isActive": bool}
    current_user: dict = Depends(authorize_roles(["admin"]))
):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid hospital ID")

    hospital = await hospitals_collection.find_one({"_id": ObjectId(id)})
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    update_data = {}
    if "isVerified" in data:
        update_data["isVerified"] = bool(data["isVerified"])
    if "isActive" in data:
        update_data["isActive"] = bool(data["isActive"])

    if update_data:
        await hospitals_collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        # Refetch
        hospital = await hospitals_collection.find_one({"_id": ObjectId(id)})

    return {
        "success": True,
        "message": "Hospital status updated successfully",
        "data": {
            "id": str(hospital["_id"]),
            "name": hospital.get("name"),
            "isVerified": hospital.get("isVerified", False),
            "isActive": hospital.get("isActive", True)
        }
    }
