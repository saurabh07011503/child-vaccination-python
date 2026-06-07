import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from app.models import ChildCreate, ChildUpdate, serialize_doc
from app.database import children_collection, parents_collection
from app.auth import get_current_user, authorize_roles
from app.data.vaccination_schedule import get_child_vaccine_schedule

router = APIRouter(prefix="/children", tags=["Child Management"])

def calculate_age_in_months(date_of_birth) -> int:
    try:
        if isinstance(date_of_birth, str):
            clean_dob = date_of_birth.replace("Z", "")
            if "T" in clean_dob:
                clean_dob = clean_dob.split("T")[0]
            dob = datetime.strptime(clean_dob, "%Y-%m-%d")
        elif isinstance(date_of_birth, datetime):
            dob = date_of_birth
        else:
            return 0
        
        today = datetime.utcnow()
        return (today.year - dob.year) * 12 + (today.month - dob.month)
    except Exception:
        return 0

def serialize_child(child: dict) -> dict:
    if not child:
        return {}
    res = serialize_doc(child)
    res["fullName"] = f"{child.get('firstName', '')} {child.get('lastName', '')}".strip()
    res["ageInMonths"] = calculate_age_in_months(child.get("dateOfBirth"))
    return res

@router.post("")
async def add_child(data: ChildCreate, current_user: dict = Depends(authorize_roles(["parent"]))):
    # Generate unique childId
    child_id_str = f"CHILD-{uuid.uuid4().hex[:8].upper()}"
    
    # Parse dateOfBirth
    dob_str = data.dateOfBirth
    try:
        # Validate date is not in the future
        clean_dob = dob_str.replace("Z", "")
        if "T" in clean_dob:
            clean_dob = clean_dob.split("T")[0]
        dob_dt = datetime.strptime(clean_dob, "%Y-%m-%d")
        if dob_dt > datetime.utcnow():
            raise HTTPException(status_code=400, detail="Date of birth cannot be in the future")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid dateOfBirth format")

    child_doc = {
        "childId": child_id_str,
        "parentId": ObjectId(current_user["id"]),
        "firstName": data.firstName,
        "lastName": data.lastName,
        "dateOfBirth": dob_dt, # store as datetime
        "gender": data.gender,
        "bloodGroup": data.bloodGroup or "Unknown",
        "birthWeight": data.birthWeight,
        "birthHeight": data.birthHeight,
        "allergies": data.allergies or [],
        "medicalConditions": data.medicalConditions or [],
        "notes": data.notes,
        "isActive": True,
        "profileImage": None,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }

    result = await children_collection.insert_one(child_doc)
    inserted_id = result.inserted_id

    # Update parent's children array
    await parents_collection.update_one(
        {"_id": ObjectId(current_user["id"])},
        {"$push": {"children": inserted_id}}
    )

    child_doc["_id"] = inserted_id
    return {
        "success": True,
        "message": "Child added successfully",
        "data": serialize_child(child_doc)
    }

@router.get("")
async def get_children(current_user: dict = Depends(authorize_roles(["parent"]))):
    cursor = children_collection.find({
        "parentId": ObjectId(current_user["id"]),
        "isActive": True
    }).sort("createdAt", -1)
    
    children = []
    async for doc in cursor:
        children.append(serialize_child(doc))

    return {
        "success": True,
        "count": len(children),
        "data": children
    }

@router.get("/{id}")
async def get_child_by_id(id: str, current_user: dict = Depends(authorize_roles(["parent"]))):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid child ID")

    child = await children_collection.find_one({
        "_id": ObjectId(id),
        "parentId": ObjectId(current_user["id"]),
        "isActive": True
    })

    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    return {
        "success": True,
        "data": serialize_child(child)
    }

@router.put("/{id}")
async def update_child(id: str, data: ChildUpdate, current_user: dict = Depends(authorize_roles(["parent"]))):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid child ID")

    child = await children_collection.find_one({
        "_id": ObjectId(id),
        "parentId": ObjectId(current_user["id"]),
        "isActive": True
    })

    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    # Update fields
    update_data = {}
    data_dict = data.dict(exclude_unset=True)
    
    for k, v in data_dict.items():
        if k == "dateOfBirth" and v is not None:
            try:
                clean_dob = v.replace("Z", "")
                if "T" in clean_dob:
                    clean_dob = clean_dob.split("T")[0]
                update_data[k] = datetime.strptime(clean_dob, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid dateOfBirth format")
        elif v is not None:
            update_data[k] = v

    if update_data:
        update_data["updatedAt"] = datetime.utcnow()
        await children_collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data}
        )
        # Fetch updated child doc
        child = await children_collection.find_one({"_id": ObjectId(id)})

    return {
        "success": True,
        "message": "Child updated successfully",
        "data": serialize_child(child)
    }

@router.delete("/{id}")
async def delete_child(id: str, current_user: dict = Depends(authorize_roles(["parent"]))):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid child ID")

    result = await children_collection.update_one(
        {"_id": ObjectId(id), "parentId": ObjectId(current_user["id"]), "isActive": True},
        {"$set": {"isActive": False, "updatedAt": datetime.utcnow()}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Child not found")

    return {
        "success": True,
        "message": "Child deleted successfully"
    }

@router.get("/{id}/vaccination-schedule")
async def get_vaccination_schedule(id: str, current_user: dict = Depends(authorize_roles(["parent"]))):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid child ID")

    child = await children_collection.find_one({
        "_id": ObjectId(id),
        "parentId": ObjectId(current_user["id"]),
        "isActive": True
    })

    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    dob = child.get("dateOfBirth")
    schedule = get_child_vaccine_schedule(dob)

    return {
        "success": True,
        "data": {
            "child": {
                "id": str(child["_id"]),
                "name": f"{child.get('firstName')} {child.get('lastName')}",
                "dateOfBirth": dob.isoformat() if isinstance(dob, datetime) else str(dob),
                "ageInMonths": calculate_age_in_months(dob)
            },
            "schedule": schedule
        }
    }
