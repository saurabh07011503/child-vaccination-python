import aiosmtplib
import base64
import urllib.request
import urllib.parse
import asyncio
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings
from datetime import datetime

async def send_email(to_email: str, subject: str, html_content: str):
    if not settings.EMAIL_USER or not settings.EMAIL_PASS:
        print("[WARNING] EMAIL_USER or EMAIL_PASS not configured. Skipping email send.")
        return
        
    message = MIMEMultipart("alternative")
    message["From"] = f'"Vaccine Tracker" <{settings.EMAIL_USER}>'
    message["To"] = to_email
    message["Subject"] = subject
    
    html_part = MIMEText(html_content, "html")
    message.attach(html_part)
    
    try:
        # Connect to Gmail SMTP via SSL on port 465
        await aiosmtplib.send(
            message,
            hostname="smtp.gmail.com",
            port=465,
            username=settings.EMAIL_USER,
            password=settings.EMAIL_PASS,
            use_tls=True
        )
        print(f"[SUCCESS] Email sent successfully to {to_email}")
    except Exception as e:
        print(f"[ERROR] Error sending email: {e}")

def _sync_send_twilio_message(to: str, body: str, is_whatsapp: bool = False):
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    from_number = settings.TWILIO_WHATSAPP_NUMBER if is_whatsapp else settings.TWILIO_FROM_NUMBER
    
    # Format phone number for Twilio (ensure E.164 format)
    clean_to = str(to).strip()
    if clean_to and not clean_to.startswith("+"):
        if len(clean_to) == 10:
            clean_to = f"+91{clean_to}" # default to India country code +91
        else:
            clean_to = f"+{clean_to}"
    
    if not account_sid or not auth_token or not from_number:
        if is_whatsapp:
            return False
        print(f"[SIMULATED SMS] To: {clean_to} | Body: {body}")
        return True

    formatted_to = f"whatsapp:{clean_to}" if is_whatsapp and not clean_to.startswith("whatsapp:") else clean_to
    formatted_from = f"whatsapp:{from_number}" if is_whatsapp and not from_number.startswith("whatsapp:") else from_number

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    
    data = urllib.parse.urlencode({
        "To": formatted_to,
        "From": formatted_from,
        "Body": body
    }).encode("utf-8")
    
    auth_str = f"{account_sid}:{auth_token}"
    b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
    
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Authorization", f"Basic {b64_auth}")
    
    try:
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            print(f"[SUCCESS] Twilio {'WhatsApp' if is_whatsapp else 'SMS'} sent. Status: {status}")
            return True
    except Exception as e:
        print(f"[ERROR] Twilio {'WhatsApp' if is_whatsapp else 'SMS'} failed: {e}")
        return False

def _sync_send_callmebot_whatsapp(to: str, body: str):
    apikey = settings.CALLMEBOT_API_KEY
    if not apikey:
        return False
    
    # CallMeBot expects phone with country code but NO "+" or spaces
    clean_phone = str(to).replace("+", "").replace(" ", "").strip()
    if len(clean_phone) == 10:
        clean_phone = f"91{clean_phone}" # India default
        
    encoded_text = urllib.parse.quote(body)
    url = f"https://api.callmebot.com/whatsapp.php?phone={clean_phone}&text={encoded_text}&apikey={apikey}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            print(f"[SUCCESS] CallMeBot WhatsApp sent to {clean_phone}. Status: {status}")
            return True
    except Exception as e:
        print(f"[ERROR] CallMeBot WhatsApp failed for {clean_phone}: {e}")
        return False

async def send_callmebot_whatsapp(to: str, body: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_send_callmebot_whatsapp, to, body)

def _sync_send_textmebot_whatsapp(to: str, body: str) -> bool:
    apikey = settings.TEXTMEBOT_API_KEY
    if not apikey:
        return False

    recipient = str(to).replace(" ", "").strip()
    if recipient and not recipient.startswith("+"):
        recipient = f"+91{recipient}" if len(recipient) == 10 else f"+{recipient}"

    url = (
        "https://api.textmebot.com/send.php?"
        + urllib.parse.urlencode({
            "recipient": recipient,
            "apikey": apikey,
            "text": body,
        })
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response:
            data = response.read().decode("utf-8", errors="replace").strip().lower()
            error_markers = (
                "error", "fail", "invalid", "not connected", "not linked", "expired",
                "dont have", "don't have", "not associated", "asociated", "addphone",
                "not active", "subscribe", "click <a href",
            )
            if any(marker in data for marker in error_markers):
                print(f"[ERROR] TextMeBot WhatsApp to {recipient}: {data[:200]}")
                print("[ERROR] Link WhatsApp in the TextMeBot email you received (see WHATSAPP_SETUP.md)")
                return False
            print(f"[SUCCESS] TextMeBot WhatsApp sent to {recipient}: {data[:120] or 'ok'}")
            return True
    except Exception as e:
        print(f"[ERROR] TextMeBot WhatsApp failed for {recipient}: {e}")
        return False


async def send_textmebot_whatsapp(to: str, body: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_send_textmebot_whatsapp, to, body)


async def send_whatsapp_message(to: str, body: str) -> bool:
    """WhatsApp: TextMeBot → Twilio sandbox → CallMeBot (self only)."""
    if settings.TEXTMEBOT_API_KEY:
        ok = await send_textmebot_whatsapp(to, body)
        if ok:
            return True
        print("[WhatsApp] TextMeBot failed; trying next provider...")

    if (
        settings.TWILIO_ACCOUNT_SID
        and settings.TWILIO_AUTH_TOKEN
        and settings.TWILIO_WHATSAPP_NUMBER
    ):
        loop = asyncio.get_event_loop()
        ok = await loop.run_in_executor(
            None, _sync_send_twilio_message, to, body, True
        )
        if ok:
            return True
        print("[WhatsApp] Twilio WhatsApp failed; trying CallMeBot if configured...")

    if settings.CALLMEBOT_API_KEY:
        ok = await send_callmebot_whatsapp(to, body)
        if ok:
            return True

    print(
        "[WhatsApp] Not configured. Use TWILIO_WHATSAPP_NUMBER (sandbox), "
        "TEXTMEBOT_API_KEY, or CALLMEBOT_API_KEY. See WHATSAPP_SETUP.md"
    )
    return False


async def send_twilio_message(to: str, body: str, is_whatsapp: bool = False):
    if is_whatsapp:
        return await send_whatsapp_message(to, body)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_send_twilio_message, to, body, False)

def format_date(date_val) -> str:
    if isinstance(date_val, str):
        # Convert iso date to readable date string
        try:
            dt = datetime.fromisoformat(date_val.replace("Z", ""))
            return dt.strftime("%a %b %d %Y")
        except:
            return date_val
    elif isinstance(date_val, datetime):
        return date_val.strftime("%a %b %d %Y")
    return str(date_val)

async def send_appointment_confirmation(appointment: dict, parent_data, child_name: str, hospital_name: str):
    parent_email = ""
    parent_phone = ""
    
    if isinstance(parent_data, dict):
        parent_email = parent_data.get("email", "")
        parent_phone = parent_data.get("phone", "")
    else:
        parent_email = str(parent_data)

    # 1. Send Email
    if parent_email:
        subject = "Vaccination Appointment Confirmation"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <h2 style="color: #2563eb;">Vaccination Appointment Confirmed!</h2>
          <p>Hello,</p>
          <p>Your vaccination appointment has been successfully booked. Here are the details:</p>
          
          <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p><strong>Child's Name:</strong> {child_name}</p>
            <p><strong>Vaccine:</strong> {appointment.get('vaccineName')}</p>
            <p><strong>Date:</strong> {format_date(appointment.get('appointmentDate'))}</p>
            <p><strong>Time:</strong> {appointment.get('appointmentTime')}</p>
            <p><strong>Hospital:</strong> {hospital_name}</p>
            <p><strong>Appointment ID:</strong> {appointment.get('appointmentId')}</p>
          </div>
          
          <p>Please arrive 15 minutes before your scheduled time and bring your child's vaccination card.</p>
          <p>If you need to reschedule or cancel, please do so at least 24 hours in advance.</p>
          <p>Best regards,<br>Vaccine Tracker Team</p>
          
          <div style="margin-top: 20px; font-size: 12px; color: #6b7280;">
            <p>This is an automated message. Please do not reply to this email.</p>
          </div>
        </div>
        """
        await send_email(parent_email, subject, html_content)

    # 2. Send SMS and WhatsApp
    if parent_phone:
        formatted_date = format_date(appointment.get("appointmentDate"))
        sms_body = f"NeoVax: Vaccination appointment for {child_name} (Vaccine: {appointment.get('vaccineName')}) has been confirmed at {hospital_name} on {formatted_date} at {appointment.get('appointmentTime')}. Bring child's vaccination card. Ref: {appointment.get('appointmentId')}"
        
        await send_twilio_message(parent_phone, sms_body, is_whatsapp=False)
        await send_whatsapp_message(parent_phone, sms_body)

def get_status_message(status: str) -> str:
    messages = {
        'Confirmed': 'Your appointment has been confirmed. We look forward to seeing you!',
        'Cancelled': 'Your appointment has been cancelled. If this was a mistake, please contact the hospital directly.',
        'Completed': "Thank you for visiting us! The vaccination has been recorded in your child's records.",
        'Rescheduled': 'Your appointment has been rescheduled. Please check the new date and time above.'
    }
    return messages.get(status, 'Your appointment status has been updated.')

async def send_appointment_status_update(appointment: dict, parent_data, child_name: str, hospital_name: str):
    parent_email = ""
    parent_phone = ""
    
    if isinstance(parent_data, dict):
        parent_email = parent_data.get("email", "")
        parent_phone = parent_data.get("phone", "")
    else:
        parent_email = str(parent_data)

    status_val = appointment.get('status', '')

    # 1. Send Email
    if parent_email:
        subject = f"Appointment {status_val} - {appointment.get('vaccineName')}"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <h2 style="color: #2563eb;">Appointment {status_val}</h2>
          <p>Hello,</p>
          <p>Your vaccination appointment status has been updated to <strong>{status_val}</strong>.</p>
          
          <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p><strong>Child's Name:</strong> {child_name}</p>
            <p><strong>Vaccine:</strong> {appointment.get('vaccineName')}</p>
            <p><strong>Date:</strong> {format_date(appointment.get('appointmentDate'))}</p>
            <p><strong>Time:</strong> {appointment.get('appointmentTime')}</p>
            <p><strong>Hospital:</strong> {hospital_name}</p>
            <p><strong>Status:</strong> {status_val}</p>
          </div>
          
          <p>{get_status_message(status_val)}</p>
          <p>Best regards,<br>Vaccine Tracker Team</p>
        </div>
        """
        await send_email(parent_email, subject, html_content)

    # 2. Send SMS and WhatsApp
    if parent_phone:
        formatted_date = format_date(appointment.get("appointmentDate"))
        status_msg = get_status_message(status_val)
        sms_body = f"NeoVax: Appointment status for {child_name} (Vaccine: {appointment.get('vaccineName')}) has been updated to {status_val}. Date: {formatted_date}, Time: {appointment.get('appointmentTime')} at {hospital_name}. {status_msg}"
        
        await send_twilio_message(parent_phone, sms_body, is_whatsapp=False)
        await send_whatsapp_message(parent_phone, sms_body)

async def send_appointment_reminder(appointment: dict, parent_data, child_name: str, hospital_name: str):
    parent_email = ""
    parent_phone = ""
    
    if isinstance(parent_data, dict):
        parent_email = parent_data.get("email", "")
        parent_phone = parent_data.get("phone", "")
    else:
        parent_email = str(parent_data)

    # 1. Send Email
    if parent_email:
        subject = f"Reminder: Vaccination Appointment in 10 Minutes - {appointment.get('vaccineName')}"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <h2 style="color: #f59e0b;">Appointment Reminder</h2>
          <p>Hello,</p>
          <p>This is a reminder that your child has a vaccination appointment scheduled in <strong>10 minutes</strong>.</p>
          
          <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p><strong>Child's Name:</strong> {child_name}</p>
            <p><strong>Vaccine:</strong> {appointment.get('vaccineName')}</p>
            <p><strong>Date:</strong> {format_date(appointment.get('appointmentDate'))}</p>
            <p><strong>Time:</strong> {appointment.get('appointmentTime')}</p>
            <p><strong>Hospital:</strong> {hospital_name}</p>
          </div>
          
          <p>Please arrive 15 minutes before your scheduled time and bring your child's vaccination card.</p>
          <p>If you cannot make it, please reschedule or cancel via the app as soon as possible.</p>
          <p>Best regards,<br>Vaccine Tracker Team</p>
        </div>
        """
        await send_email(parent_email, subject, html_content)

    # 2. Send SMS and WhatsApp
    if parent_phone:
        sms_body = f"NeoVax Reminder: Vaccination appointment for {child_name} (Vaccine: {appointment.get('vaccineName')}) at {hospital_name} is scheduled in 10 minutes (at {appointment.get('appointmentTime')}). Please arrive on time."
        
        await send_twilio_message(parent_phone, sms_body, is_whatsapp=False)
        await send_whatsapp_message(parent_phone, sms_body)
