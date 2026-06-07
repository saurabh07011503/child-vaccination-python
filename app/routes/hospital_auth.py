from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from app.models import HospitalSignup, HospitalLogin, serialize_doc
from app.database import hospitals_collection
from app.auth import hash_password, verify_password, create_access_token, get_current_user, authorize_roles

router = APIRouter(prefix="/auth/hospital", tags=["Hospital Auth"])

@router.post("/signup")
async def signup(data: HospitalSignup):
    # Check if hospital already exists
    existing = await hospitals_collection.find_one({
        "$or": [
            {"email": data.email},
            {"phone": data.phone},
            {"registrationNumber": data.registrationNumber}
        ]
    })

    if existing:
        if existing.get("email") == data.email:
            msg = "Email already registered"
        elif existing.get("phone") == data.phone:
            msg = "Phone number already registered"
        else:
            msg = "Registration number already exists"
        raise HTTPException(status_code=400, detail=msg)

    # Convert complex pydantic schemas to python dicts
    address_dict = data.address.dict() if data.address else None
    operating_hours_dict = data.operatingHours.dict() if data.operatingHours else None

    # Create hospital doc (auto-verified for testing)
    hospital_doc = {
        "name": data.name,
        "email": data.email,
        "phone": data.phone,
        "password": hash_password(data.password),
        "registrationNumber": data.registrationNumber,
        "address": address_dict,
        "location": data.location,
        "facilities": data.facilities,
        "operatingHours": operating_hours_dict,
        "isVerified": True, # Auto-verify for testing
        "isActive": True,
        "profileImage": None
    }

    result = await hospitals_collection.insert_one(hospital_doc)
    hospital_id = str(result.inserted_id)

    # Generate token
    token = create_access_token({"id": hospital_id, "userType": "hospital"})

    return {
        "success": True,
        "message": "Hospital registered successfully and auto-verified.",
        "data": {
            "token": token,
            "user": {
                "id": hospital_id,
                "name": data.name,
                "email": data.email,
                "phone": data.phone,
                "registrationNumber": data.registrationNumber,
                "address": address_dict,
                "isVerified": True,
                "userType": "hospital"
            }
        }
    }

@router.post("/login")
async def login(data: HospitalLogin):
    hospital = await hospitals_collection.find_one({"email": data.email})

    if not hospital:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not hospital.get("isActive", True):
        raise HTTPException(status_code=403, detail="Account is deactivated. Please contact support.")

    if not verify_password(data.password, hospital["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    hospital_id = str(hospital["_id"])
    token = create_access_token({"id": hospital_id, "userType": "hospital"})

    return {
        "success": True,
        "message": "Login successful",
        "data": {
            "token": token,
            "user": {
                "id": hospital_id,
                "name": hospital.get("name"),
                "email": hospital.get("email"),
                "phone": hospital.get("phone"),
                "registrationNumber": hospital.get("registrationNumber"),
                "address": hospital.get("address"),
                "location": hospital.get("location"),
                "facilities": hospital.get("facilities"),
                "operatingHours": hospital.get("operatingHours"),
                "isVerified": hospital.get("isVerified", False),
                "profileImage": hospital.get("profileImage"),
                "userType": "hospital"
            }
        }
    }

@router.get("/profile")
async def get_profile(current_user: dict = Depends(authorize_roles(["hospital"]))):
    hospital = await hospitals_collection.find_one({"_id": ObjectId(current_user["id"])})

    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    return {
        "success": True,
        "data": {
            "id": str(hospital["_id"]),
            "name": hospital.get("name"),
            "email": hospital.get("email"),
            "phone": hospital.get("phone"),
            "registrationNumber": hospital.get("registrationNumber"),
            "address": hospital.get("address"),
            "location": hospital.get("location"),
            "facilities": hospital.get("facilities"),
            "operatingHours": hospital.get("operatingHours"),
            "isVerified": hospital.get("isVerified", False),
            "profileImage": hospital.get("profileImage"),
            "userType": "hospital"
        }
    }
