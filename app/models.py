from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Any, Dict
from datetime import datetime
from bson import ObjectId

# Pydantic v2 helper to validate/serialize MongoDB ObjectIds as strings
class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return str(v)

def serialize_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if doc is None:
        return None
    serialized = {}
    for key, value in doc.items():
        if key == "_id":
            serialized["_id"] = str(value)
            serialized["id"] = str(value)
        elif isinstance(value, ObjectId):
            serialized[key] = str(value)
        elif isinstance(value, list):
            serialized[key] = [str(item) if isinstance(item, ObjectId) else serialize_doc(item) if isinstance(item, dict) else item for item in value]
        elif isinstance(value, datetime):
            serialized[key] = value.isoformat()
        elif isinstance(value, dict):
            serialized[key] = serialize_doc(value)
        else:
            serialized[key] = value
    return serialized

def serialize_list(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [serialize_doc(doc) for doc in docs if doc is not None]

# Parent Schemas
class ParentSignup(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    phone: str = Field(..., pattern=r"^[0-9]{10}$")
    password: str = Field(..., min_length=6)
    address: Optional[str] = None

class ParentLogin(BaseModel):
    email: EmailStr
    password: str

# Hospital Schemas
class WeekdayHours(BaseModel):
    open: str
    close: str

class WeekendHours(BaseModel):
    open: str
    close: str

class OperatingHours(BaseModel):
    weekdays: WeekdayHours
    weekends: WeekendHours

class HospitalAddress(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: str = "India"

class HospitalSignup(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(..., pattern=r"^[0-9]{10}$")
    password: str = Field(..., min_length=6)
    registrationNumber: str
    address: Optional[HospitalAddress] = None
    location: Optional[Dict[str, Any]] = None  # GeoJSON Point
    facilities: Optional[List[str]] = []
    operatingHours: Optional[OperatingHours] = None

class HospitalLogin(BaseModel):
    email: EmailStr
    password: str

# Child Schemas
class ChildCreate(BaseModel):
    firstName: str
    lastName: str
    dateOfBirth: str # ISO Date string "YYYY-MM-DD"
    gender: str # 'Male', 'Female', 'Other'
    bloodGroup: Optional[str] = "Unknown"
    birthWeight: float # in kg
    birthHeight: float # in cm
    allergies: Optional[List[str]] = []
    medicalConditions: Optional[List[str]] = []
    notes: Optional[str] = ""

class ChildUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    dateOfBirth: Optional[str] = None
    gender: Optional[str] = None
    bloodGroup: Optional[str] = None
    birthWeight: Optional[float] = None
    birthHeight: Optional[float] = None
    allergies: Optional[List[str]] = None
    medicalConditions: Optional[List[str]] = None
    notes: Optional[str] = None
    profileImage: Optional[str] = None

# Appointment Schemas
class AppointmentBook(BaseModel):
    childId: str
    hospitalId: str
    vaccineId: str
    vaccineName: str
    appointmentDate: str # ISO Date string
    appointmentTime: str # "HH:MM"
    notes: Optional[str] = ""

class AppointmentReschedule(BaseModel):
    appointmentDate: str
    appointmentTime: str
    rescheduledReason: Optional[str] = ""

class AppointmentStatusUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    completedDate: Optional[str] = None
    rescheduledReason: Optional[str] = None

# Chat Schemas
class ChatMessage(BaseModel):
    message: str
    history: Optional[List[Dict[str, Any]]] = []
