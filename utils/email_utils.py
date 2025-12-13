# at top of routers/bookings.py
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import timezone

from models import Booking, Member, Car, Airport

def generate_booking_ics(booking: Booking, car: Car, airport: Airport) -> str:
    """
    Generate a simple .ics calendar event for the booking.
    All times are treated as UTC here; adjust if you want local zones.
    """
    dt_start = booking.start_time.astimezone(timezone.utc)
    dt_end = booking.end_time.astimezone(timezone.utc)

    def fmt(dt):
        return dt.strftime("%Y%m%dT%H%M%SZ")  # UTC format

    uid = f"booking-{booking.bookings_id}@flydriveconnect"

    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//FlyDrive Connect//EN
BEGIN:VEVENT
UID:{uid}
SUMMARY:FlyDrive Booking – {car.make_model or car.registration}
DTSTART:{fmt(dt_start)}
DTEND:{fmt(dt_end)}
LOCATION:{airport.name}
DESCRIPTION:Your FlyDrive Connect booking is confirmed. Car: {car.make_model or car.registration}, Airport: {airport.name}.
END:VEVENT
END:VCALENDAR
"""
    return ics


def send_booking_confirmation_email(
    member: Member,
    booking: Booking,
    car: Car,
    airport: Airport,
):
    """
    Simple SMTP-based mailer.
    You can back this with SES SMTP, SendGrid, etc.
    Environment variables:
        SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, FROM_EMAIL
    For now, if not configured, just log and return.
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("FROM_EMAIL", "no-reply@flydriveconnect.com")

    if not (smtp_host and smtp_user and smtp_pass):
        # Not configured – avoid crashing
        print("Email not sent: SMTP not configured")
        return

    to_email = member.email
    if not to_email:
        print("Email not sent: member has no email")
        return

    subject = f"Your FlyDrive Booking #{booking.bookings_id}"
    body_text = f"""
Hi {member.name or ''},

Your FlyDrive booking is confirmed.

Car: {car.make_model or car.registration}
Airport: {airport.name}
Start: {booking.start_time}
End:   {booking.end_time}
Status: {booking.status}

You can also add this to your calendar using the attached event.

Safe travels,
FlyDrive Connect
""".strip()

    # Build email with .ics attachment
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    # Plain text body
    msg.attach(MIMEText(body_text, "plain"))

    # ICS attachment
    ics_content = generate_booking_ics(booking, car, airport)
    part = MIMEBase("text", "calendar", method="REQUEST", name="booking.ics")
    part.set_payload(ics_content)
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", 'attachment; filename="booking.ics"')
    msg.attach(part)

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(from_email, [to_email], msg.as_string())
