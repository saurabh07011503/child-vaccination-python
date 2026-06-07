from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from app.models import ParentSignup, ParentLogin, serialize_doc
from app.database import parents_collection, children_collection
from app.auth import hash_password, verify_password, create_access_token, get_current_user, authorize_roles

router = APIRouter(prefix="/auth/parent", tags=["Parent Auth"])

@router.post("/signup")
async def signup(data: ParentSignup):
    print("[DEBUG] Incoming signup data:", data.dict())
    # Check if parent already exists
    existing = await parents_collection.find_one({
        "$or": [{"email": data.email}, {"phone": data.phone}]
    })

    if existing:
        msg = "Email already registered" if existing.get("email") == data.email else "Phone number already registered"
        raise HTTPException(status_code=400, detail=msg)

    # Create parent doc
    parent_doc = {
        "name": data.name,
        "email": data.email,
        "phone": data.phone,
        "password": hash_password(data.password),
        "address": data.address,
        "isActive": True,
        "children": [],
        "profileImage": None
    }

    result = await parents_collection.insert_one(parent_doc)
    parent_id = str(result.inserted_id)

    # Generate token
    token = create_access_token({"id": parent_id, "userType": "parent"})

    return {
        "success": True,
        "message": "Parent registered successfully",
        "data": {
            "token": token,
            "user": {
                "id": parent_id,
                "name": data.name,
                "email": data.email,
                "phone": data.phone,
                "address": data.address,
                "userType": "parent"
            }
        }
    }

@router.post("/login")
async def login(data: ParentLogin):
    parent = await parents_collection.find_one({"email": data.email})

    if not parent:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not parent.get("isActive", True):
        raise HTTPException(status_code=403, detail="Account is deactivated. Please contact support.")

    if not verify_password(data.password, parent["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    parent_id = str(parent["_id"])
    token = create_access_token({"id": parent_id, "userType": "parent"})

    return {
        "success": True,
        "message": "Login successful",
        "data": {
            "token": token,
            "user": {
                "id": parent_id,
                "name": parent.get("name"),
                "email": parent.get("email"),
                "phone": parent.get("phone"),
                "address": parent.get("address"),
                "profileImage": parent.get("profileImage"),
                "userType": "parent"
            }
        }
    }

@router.get("/profile")
async def get_profile(current_user: dict = Depends(authorize_roles(["parent"]))):
    parent = await parents_collection.find_one({"_id": ObjectId(current_user["id"])})

    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")

    # Populate children
    children = []
    # If the parent has a children list of ObjectIds
    children_ids = parent.get("children", [])
    if children_ids:
        # Some parent records might store child IDs as strings or ObjectIds.
        # Let's support both to be safe.
        obj_ids = []
        for cid in children_ids:
            try:
                obj_ids.append(ObjectId(cid) if isinstance(cid, (str, ObjectId)) else cid)
            except:
                pass
        cursor = children_collection.find({"_id": {"$in": obj_ids}})
        async for c in cursor:
            children.append(serialize_doc(c))

    return {
        "success": True,
        "data": {
            "id": str(parent["_id"]),
            "name": parent.get("name"),
            "email": parent.get("email"),
            "phone": parent.get("phone"),
            "address": parent.get("address"),
            "profileImage": parent.get("profileImage"),
            "children": children,
            "userType": "parent"
        }
    }
