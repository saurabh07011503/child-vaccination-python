from fastapi import APIRouter, Depends, HTTPException, status, Query
from bson import ObjectId
from datetime import datetime
from typing import Optional
from app.models import AppointmentBook, AppointmentReschedule, AppointmentStatusUpdate, serialize_doc, serialize_list
from app.database import appointments_collection, children_collection, hospitals_collection, parents_collection
from app.auth import get_current_user, authorize_roles
from app.utils.email_service import send_appointment_confirmation, send_appointment_status_update

router = APIRouter(prefix="/appointments", tags=["Appointments Management"])

async def populate_appointment(apt: dict) -> dict:
    if not apt:
        return {}
    apt = serialize_doc(apt)
    
    if apt.get("childId"):
        child = await children_collection.find_one({"_id": ObjectId(apt["childId"])})
        if child:
            apt["childId"] = {
                "_id": str(child["_id"]),
                "id": str(child["_id"]),
                "childId": child.get("childId"),
                "firstName": child.get("firstName"),
                "lastName": child.get("lastName"),
                "dateOfBirth": child.get("dateOfBirth").isoformat() if isinstance(child.get("dateOfBirth"), datetime) else str(child.get("dateOfBirth")),
                "gender": child.get("gender"),
                "bloodGroup": child.get("bloodGroup"),
                "allergies": child.get("allergies"),
                "medicalConditions": child.get("medicalConditions")
            }
            
    if apt.get("parentId"):
        parent = await parents_collection.find_one({"_id": ObjectId(apt["parentId"])})
        if parent:
            apt["parentId"] = {
                "_id": str(parent["_id"]),
                "id": str(parent["_id"]),
                "name": parent.get("name"),
                "phone": parent.get("phone"),
                "email": parent.get("email"),
                "address": parent.get("address")
            }
            
    if apt.get("hospitalId"):
        hospital = await hospitals_collection.find_one({"_id": ObjectId(apt["hospitalId"])})
        if hospital:
            apt["hospitalId"] = {
                "_id": str(hospital["_id"]),
                "id": str(hospital["_id"]),
                "name": hospital.get("name"),
                "address": hospital.get("address"),
                "phone": hospital.get("phone"),
                "email": hospital.get("email")
            }
    return apt

@router.post("")
async def book_appointment(data: AppointmentBook, current_user: dict = Depends(authorize_roles(["parent"]))):
    # Verify child belongs to parent
    if not ObjectId.is_valid(data.childId):
        raise HTTPException(status_code=400, detail="Invalid childId")
    if not ObjectId.is_valid(data.hospitalId):
        raise HTTPException(status_code=400, detail="Invalid hospitalId")

    child = await children_collection.find_one({
        "_id": ObjectId(data.childId),
        "parentId": ObjectId(current_user["id"]),
        "isActive": True
    })
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    # Verify hospital exists
    hospital = await hospitals_collection.find_one({"_id": ObjectId(data.hospitalId)})
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    # Parse and establish start/end of day to check capacity (max 20 per day)
    try:
        clean_date = data.appointmentDate.replace("Z", "")
        if "T" in clean_date:
            clean_date = clean_date.split("T")[0]
        apt_date = datetime.strptime(clean_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    start_of_day = datetime(apt_date.year, apt_date.month, apt_date.day, 0, 0, 0)
    end_of_day = datetime(apt_date.year, apt_date.month, apt_date.day, 23, 59, 59, 999999)

    appointments_count = await appointments_collection.count_documents({
        "hospitalId": ObjectId(data.hospitalId),
        "appointmentDate": {
            "$gte": start_of_day,
            "$lte": end_of_day
        },
        "status": {"$in": ["Pending", "Confirmed"]}
    })

    if appointments_count >= 20:
        raise HTTPException(
            status_code=400,
            detail="Hospital has reached maximum capacity for this date. Please choose another date."
        )

    # Create new appointment
    appointment_id_str = f"APPT-{int(datetime.utcnow().timestamp() * 1000)}"
    
    appointment_doc = {
        "appointmentId": appointment_id_str,
        "childId": ObjectId(data.childId),
        "parentId": ObjectId(current_user["id"]),
        "hospitalId": ObjectId(data.hospitalId),
        "vaccineId": data.vaccineId,
        "vaccineName": data.vaccineName,
        "appointmentDate": apt_date,
        "appointmentTime": data.appointmentTime,
        "status": "Pending",
        "notes": data.notes or "",
        "reminderSent": False,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }

    result = await appointments_collection.insert_one(appointment_doc)
    appointment_doc["_id"] = result.inserted_id

    # Send confirmation email
    try:
        parent = await parents_collection.find_one({"_id": ObjectId(current_user["id"])})
        if parent:
            await send_appointment_confirmation(
                appointment_doc,
                parent,
                f"{child.get('firstName')} {child.get('lastName')}",
                hospital.get("name")
            )
    except Exception as email_err:
        print(f"Error sending notifications: {email_err}")

    # Return populated appointment
    populated = await populate_appointment(appointment_doc)
    return {
        "success": True,
        "message": "Appointment booked successfully",
        "data": populated
    }

@router.get("/parent")
async def get_parent_appointments(
    status: Optional[str] = None,
    childId: Optional[str] = None,
    current_user: dict = Depends(authorize_roles(["parent"]))
):
    query = {"parentId": ObjectId(current_user["id"])}
    if status:
        query["status"] = status
    if childId:
        if ObjectId.is_valid(childId):
            query["childId"] = ObjectId(childId)

    cursor = appointments_collection.find(query).sort("appointmentDate", -1)
    appointments = []
    async for doc in cursor:
        appointments.append(await populate_appointment(doc))

    return {
        "success": True,
        "count": len(appointments),
        "data": appointments
    }

@router.get("/hospitals")
async def get_available_hospitals(current_user: dict = Depends(authorize_roles(["parent"]))):
    # Retrieve active hospitals
    cursor = hospitals_collection.find(
        {"isActive": True},
        {"name": 1, "address": 1, "phone": 1, "email": 1, "facilities": 1, "operatingHours": 1, "location": 1}
    )
    hospitals = []
    async for h in cursor:
        hospitals.append(serialize_doc(h))

    return {
        "success": True,
        "count": len(hospitals),
        "data": hospitals
    }

@router.get("/hospital")
async def get_hospital_appointments(
    status: Optional[str] = None,
    date: Optional[str] = None,
    current_user: dict = Depends(authorize_roles(["hospital"]))
):
    query = {"hospitalId": ObjectId(current_user["id"])}
    if status:
        query["status"] = status
    
    if date:
        try:
            clean_date = date.replace("Z", "")
            if "T" in clean_date:
                clean_date = clean_date.split("T")[0]
            parsed_date = datetime.strptime(clean_date, "%Y-%m-%d")
            start_of_day = datetime(parsed_date.year, parsed_date.month, parsed_date.day, 0, 0, 0)
            end_of_day = datetime(parsed_date.year, parsed_date.month, parsed_date.day, 23, 59, 59, 999999)
            query["appointmentDate"] = {"$gte": start_of_day, "$lte": end_of_day}
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")

    cursor = appointments_collection.find(query).sort([("appointmentDate", 1), ("appointmentTime", 1)])
    appointments = []
    async for doc in cursor:
        appointments.append(await populate_appointment(doc))

    return {
        "success": True,
        "count": len(appointments),
        "data": appointments
    }

@router.get("/hospital/stats")
async def get_hospital_stats(current_user: dict = Depends(authorize_roles(["hospital"]))):
    h_id = ObjectId(current_user["id"])
    
    today = datetime.utcnow()
    start_of_today = datetime(today.year, today.month, today.day, 0, 0, 0)
    end_of_today = datetime(today.year, today.month, today.day, 23, 59, 59, 999999)

    today_count = await appointments_collection.count_documents({
        "hospitalId": h_id,
        "appointmentDate": {"$gte": start_of_today, "$lte": end_of_today}
    })
    
    pending_count = await appointments_collection.count_documents({
        "hospitalId": h_id,
        "status": "Pending"
    })
    
    confirmed_count = await appointments_collection.count_documents({
        "hospitalId": h_id,
        "status": "Confirmed"
    })
    
    completed_count = await appointments_collection.count_documents({
        "hospitalId": h_id,
        "status": "Completed"
    })
    
    total_count = await appointments_collection.count_documents({
        "hospitalId": h_id
    })

    return {
        "success": True,
        "data": {
            "today": today_count,
            "pending": pending_count,
            "confirmed": confirmed_count,
            "completed": completed_count,
            "total": total_count
        }
    }

@router.get("/{id}")
async def get_appointment_by_id(id: str, current_user: dict = Depends(get_current_user)):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid appointment ID")

    appointment = await appointments_collection.find_one({"_id": ObjectId(id)})
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Access control: user must be the parent or the hospital
    if (str(appointment.get("parentId")) != current_user["id"] and 
        str(appointment.get("hospitalId")) != current_user["id"]):
        raise HTTPException(status_code=403, detail="Not authorized to view this appointment")

    populated = await populate_appointment(appointment)
    return {
        "success": True,
        "data": populated
    }

@router.put("/{id}/reschedule")
async def reschedule_appointment(
    id: str,
    data: AppointmentReschedule,
    current_user: dict = Depends(authorize_roles(["parent"]))
):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid appointment ID")

    appointment = await appointments_collection.find_one({
        "_id": ObjectId(id),
        "parentId": ObjectId(current_user["id"])
    })

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Check capacity for new date
    try:
        clean_date = data.appointmentDate.replace("Z", "")
        if "T" in clean_date:
            clean_date = clean_date.split("T")[0]
        apt_date = datetime.strptime(clean_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")

    start_of_day = datetime(apt_date.year, apt_date.month, apt_date.day, 0, 0, 0)
    end_of_day = datetime(apt_date.year, apt_date.month, apt_date.day, 23, 59, 59, 999999)

    appointments_count = await appointments_collection.count_documents({
        "hospitalId": appointment["hospitalId"],
        "appointmentDate": {
            "$gte": start_of_day,
            "$lte": end_of_day
        },
        "status": {"$in": ["Pending", "Confirmed"]},
        "_id": {"$ne": appointment["_id"]} # Exclude current appointment
    })

    if appointments_count >= 20:
        raise HTTPException(
            status_code=400,
            detail="Hospital has reached maximum capacity for this date. Please choose another date."
        )

    # Perform update
    old_date = appointment.get("appointmentDate")
    await appointments_collection.update_one(
        {"_id": appointment["_id"]},
        {"$set": {
            "rescheduledFrom": old_date,
            "appointmentDate": apt_date,
            "appointmentTime": data.appointmentTime,
            "rescheduledReason": data.rescheduledReason,
            "status": "Rescheduled",
            "reminderSent": False, # Reset reminder state on reschedule
            "updatedAt": datetime.utcnow()
        }}
    )

    updated_appointment = await appointments_collection.find_one({"_id": appointment["_id"]})

    # Send status email notification
    try:
        child = await children_collection.find_one({"_id": appointment["childId"]})
        hospital = await hospitals_collection.find_one({"_id": appointment["hospitalId"]})
        parent = await parents_collection.find_one({"_id": appointment["parentId"]})
        
        if parent and child and hospital:
            await send_appointment_status_update(
                updated_appointment,
                parent,
                f"{child.get('firstName')} {child.get('lastName')}",
                hospital.get("name")
            )
    except Exception as email_err:
        print(f"Error sending notifications: {email_err}")

    populated = await populate_appointment(updated_appointment)
    return {
        "success": True,
        "message": "Appointment rescheduled successfully",
        "data": populated
    }

@router.put("/{id}/cancel")
async def cancel_appointment(
    id: str,
    data: dict, # Can contain {"cancellationReason": "..."}
    current_user: dict = Depends(authorize_roles(["parent"]))
):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid appointment ID")

    appointment = await appointments_collection.find_one({
        "_id": ObjectId(id),
        "parentId": ObjectId(current_user["id"])
    })

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    reason = data.get("cancellationReason", "")

    await appointments_collection.update_one(
        {"_id": appointment["_id"]},
        {"$set": {
            "status": "Cancelled",
            "cancellationReason": reason,
            "updatedAt": datetime.utcnow()
        }}
    )

    updated_appointment = await appointments_collection.find_one({"_id": appointment["_id"]})
    populated = await populate_appointment(updated_appointment)
    
    # Send status email notification
    try:
        child = await children_collection.find_one({"_id": appointment["childId"]})
        hospital = await hospitals_collection.find_one({"_id": appointment["hospitalId"]})
        parent = await parents_collection.find_one({"_id": appointment["parentId"]})
        
        if parent and child and hospital:
            await send_appointment_status_update(
                updated_appointment,
                parent,
                f"{child.get('firstName')} {child.get('lastName')}",
                hospital.get("name")
            )
    except Exception as email_err:
        print(f"Error sending notifications: {email_err}")

    return {
        "success": True,
        "message": "Appointment cancelled successfully",
        "data": populated
    }

@router.put("/{id}/status")
async def update_appointment_status(
    id: str,
    data: AppointmentStatusUpdate,
    current_user: dict = Depends(authorize_roles(["hospital"]))
):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid appointment ID")

    appointment = await appointments_collection.find_one({
        "_id": ObjectId(id),
        "hospitalId": ObjectId(current_user["id"])
    })

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    old_status = appointment.get("status")
    update_data = {}
    
    if data.status:
        update_data["status"] = data.status
        
    if data.notes is not None:
        update_data["notes"] = data.notes

    if data.status == "Completed":
        comp_date = data.completedDate or datetime.utcnow().isoformat()
        try:
            update_data["completedDate"] = datetime.fromisoformat(comp_date.replace("Z", ""))
        except:
            update_data["completedDate"] = datetime.utcnow()
            
    if data.status == "Rescheduled":
        update_data["rescheduledFrom"] = appointment.get("appointmentDate")
        if data.rescheduledReason:
            update_data["rescheduledReason"] = data.rescheduledReason

    if update_data:
        update_data["updatedAt"] = datetime.utcnow()
        await appointments_collection.update_one(
            {"_id": appointment["_id"]},
            {"$set": update_data}
        )
        # Refetch
        appointment = await appointments_collection.find_one({"_id": appointment["_id"]})

    # Send status email notification if status changed
    new_status = appointment.get("status")
    if old_status != new_status and new_status in ["Confirmed", "Cancelled", "Completed", "Rescheduled"]:
        try:
            child = await children_collection.find_one({"_id": appointment["childId"]})
            hospital = await hospitals_collection.find_one({"_id": appointment["hospitalId"]})
            parent = await parents_collection.find_one({"_id": appointment["parentId"]})
            
            if parent and child and hospital:
                await send_appointment_status_update(
                    appointment,
                    parent,
                    f"{child.get('firstName')} {child.get('lastName')}",
                    hospital.get("name")
                )
        except Exception as email_err:
            print(f"Error sending status notifications: {email_err}")

    populated = await populate_appointment(appointment)
    return {
        "success": True,
        "message": "Appointment status updated successfully",
        "data": populated
    }
