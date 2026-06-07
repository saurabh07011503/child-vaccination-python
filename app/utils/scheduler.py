import pytz
import asyncio
from datetime import datetime
from bson import ObjectId
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import appointments_collection, children_collection, hospitals_collection, parents_collection
from app.utils.email_service import send_appointment_reminder

async def process_reminders():
    try:
        kolkata = pytz.timezone('Asia/Kolkata')
        # Get timezone-aware current time in Kolkata
        now_ist = datetime.now(kolkata)
        
        # Query matching the Node.js implementation:
        # pending/confirmed status and reminderSent not true
        cursor = appointments_collection.find({
            "status": {"$in": ["Pending", "Confirmed"]},
            "reminderSent": {"$ne": True}
        })
        
        async for apt in cursor:
            try:
                apt_date = apt.get("appointmentDate")
                if not apt_date:
                    continue
                
                # Parse date if string, otherwise use datetime object
                if isinstance(apt_date, str):
                    clean_date = apt_date.replace("Z", "")
                    if "T" in clean_date:
                        clean_date = clean_date.split("T")[0]
                    apt_datetime = datetime.strptime(clean_date, "%Y-%m-%d")
                else:
                    apt_datetime = apt_date
                
                apt_time_str = apt.get("appointmentTime")
                if not apt_time_str:
                    continue
                
                # Split HH:MM
                try:
                    hours, minutes = map(int, apt_time_str.split(':'))
                except ValueError:
                    # Ignore invalid time format
                    continue
                
                # Create a timezone-aware datetime for the appointment in Asia/Kolkata
                apt_dt_ist = kolkata.localize(datetime(
                    year=apt_datetime.year,
                    month=apt_datetime.month,
                    day=apt_datetime.day,
                    hour=hours,
                    minute=minutes,
                    second=0
                ))
                
                # Calculate difference in minutes
                diff_td = apt_dt_ist - now_ist
                diff_minutes = diff_td.total_seconds() / 60.0
                
                # If appointment is in 10 minutes (with 10-minute tolerance for missed ones)
                if 0 <= diff_minutes <= 10:
                    child = await children_collection.find_one({"_id": ObjectId(apt.get("childId"))})
                    hospital = await hospitals_collection.find_one({"_id": ObjectId(apt.get("hospitalId"))})
                    parent = await parents_collection.find_one({"_id": ObjectId(apt.get("parentId"))})
                    
                    if parent and child and hospital:
                        child_name = f"{child.get('firstName')} {child.get('lastName')}"
                        await send_appointment_reminder(
                            apt,
                            parent,
                            child_name,
                            hospital.get("name")
                        )
                        
                        # Mark as sent
                        await appointments_collection.update_one(
                            {"_id": apt["_id"]},
                            {"$set": {"reminderSent": True}}
                        )
                        print(f"[SUCCESS] Sent 10-min reminder for {child_name}'s appointment at {apt_time_str}")
            except Exception as inner_e:
                print(f"Error processing reminder for appointment {apt.get('_id')}: {inner_e}")
    except Exception as e:
        print(f"Error running appointment reminder scheduler: {e}")

# Async IOScheduler initialization
scheduler = AsyncIOScheduler(timezone=pytz.timezone('Asia/Kolkata'))

def start_scheduler():
    # Run every minute
    scheduler.add_job(process_reminders, 'cron', minute='*')
    scheduler.start()
    
    # Run once immediately on startup with a 5-second delay to ensure DB is connected
    async def delayed_startup_check():
        await asyncio.sleep(5)
        print("Starting real-time 10-minute appointment reminder service (Python)...")
        await process_reminders()
        
    loop = asyncio.get_event_loop()
    if loop.is_running():
        loop.create_task(delayed_startup_check())
    else:
        loop.run_until_complete(delayed_startup_check())
    
    print("[INFO] 10-minute reminder Cron job initialized (Asia/Kolkata)")
