import os
import cv2
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
import threading
from datetime import datetime
from fire_smoke_detection import detect_fire_smoke
import pandas as pd
import pygame

# ==============================
# Streamlit page setup
# ==============================
st.set_page_config(page_title="🔥 Fire & Smoke Detection", layout="wide")
st.title("🔥 Fire & Smoke Detection System")
st.write("Real-time detection using OpenCV + Streamlit")

# ==============================
# Initialize pygame for alarm
# ==============================
pygame.mixer.init()
alarm_running = False  # global flag

def start_alarm():
    global alarm_running
    alarm_running = True

    alarm_path = os.path.join(os.getcwd(), "alarm.wav.wav")
    if not os.path.exists(alarm_path):
        st.warning(
            f"⚠️ Alarm file not found: {alarm_path}\n"
            "Please place your alarm.wav file in the same folder as app.py"
        )
        alarm_running = False
        return

    pygame.mixer.music.load(alarm_path)
    pygame.mixer.music.play(-1)  # loop indefinitely

def stop_alarm():
    global alarm_running
    alarm_running = False
    pygame.mixer.music.stop()

# ==============================
# Alert log file
# ==============================
ALERT_LOG_FILE = "alert_log.csv"

def log_alert(alert_msg, severity, image_path=None):
    from csv import writer
    clean_msg = alert_msg.encode("ascii", "ignore").decode() if alert_msg else ""
    new_entry = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        clean_msg,
        severity,
        image_path or ""
    ]
    file_exists = os.path.exists(ALERT_LOG_FILE)
    with open(ALERT_LOG_FILE, "a", newline="", encoding="utf-8") as f:
        w = writer(f)
        if not file_exists:
            w.writerow(["Timestamp", "Alert", "Severity", "Image"])
        w.writerow(new_entry)

def read_alerts():
    if not os.path.exists(ALERT_LOG_FILE):
        return None
    return pd.read_csv(ALERT_LOG_FILE, encoding="utf-8")

# ==============================
# Email Function
# ==============================
def send_email(alert_msg, severity):
    try:
        sender = st.session_state.email_sender
        recipient = st.session_state.email_recipient
        password = st.session_state.email_password
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = recipient
        msg["Subject"] = "🔥 Fire/Smoke Alert"
        body = f"{alert_msg}\nSeverity: {severity}\nTime: {datetime.now()}"
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        st.warning(f"Email failed: {e}")

# ==============================
# WhatsApp Function (Twilio)
# ==============================
def send_whatsapp(alert_msg, severity):
    try:
        client = Client(st.session_state.twilio_sid, st.session_state.twilio_token)
        body = f"{alert_msg}\nSeverity: {severity}\nTime: {datetime.now()}"
        client.messages.create(
            body=body,
            from_=st.session_state.twilio_from,
            to=st.session_state.twilio_to
        )
    except Exception as e:
        st.warning(f"WhatsApp failed: {e}")

# ==============================
# Sidebar Config & Test Buttons
# ==============================
st.sidebar.header("🔧 Notification Settings")

st.sidebar.subheader("Email")
st.session_state.email_sender = st.sidebar.text_input("Sender Email", "your_email@gmail.com")
st.session_state.email_recipient = st.sidebar.text_input("Recipient Email", "recipient@gmail.com")
st.session_state.email_password = st.sidebar.text_input("App Password", "", type="password")

st.sidebar.subheader("WhatsApp (Twilio)")
st.session_state.twilio_sid = st.sidebar.text_input("Twilio SID", "")
st.session_state.twilio_token = st.sidebar.text_input("Twilio Auth Token", "", type="password")
st.session_state.twilio_from = st.sidebar.text_input("From (e.g., whatsapp:+1415XXXXXXX)", "")
st.session_state.twilio_to = st.sidebar.text_input("To (e.g., whatsapp:+91XXXXXXXXXX)", "")

st.sidebar.subheader("🛠 Test Notifications")
if st.sidebar.button("🔔 Test Alarm"):
    start_alarm()
if st.sidebar.button("📨 Test Email"):
    send_email("Test email alert", 1)
    st.sidebar.success("✅ Test email sent")
if st.sidebar.button("💬 Test WhatsApp"):
    send_whatsapp("Test WhatsApp alert", 1)
    st.sidebar.success("✅ Test WhatsApp sent")

st.sidebar.subheader("🛑 Alarm Control")
if st.sidebar.button("🛑 Stop Alarm"):
    stop_alarm()
    st.sidebar.success("Alarm stopped")

# ==============================
# Fire Detection UI
# ==============================
run = st.checkbox("Start CCTV Detection")
FRAME_WINDOW = st.image([])
alert_placeholder = st.empty()
history_placeholder = st.empty()

camera = cv2.VideoCapture(0)

while run:
    ret, frame = camera.read()
    if not ret:
        st.write("⚠️ Camera not available.")
        break

    output_frame, alert_msg, severity = detect_fire_smoke(frame)

    FRAME_WINDOW.image(cv2.cvtColor(output_frame, cv2.COLOR_BGR2RGB))

    if alert_msg:
        alert_text = f"{alert_msg} (Severity: {severity})"
        alert_placeholder.error(alert_text)

        # Save snapshot
        image_filename = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        cv2.imwrite(image_filename, frame)

        # Log alert
        log_alert(alert_msg, severity, image_filename)

        # Update alert history
        alerts = read_alerts()
        if alerts is not None:
            history_placeholder.dataframe(alerts)

        # Start looping alarm if not already running
        if not alarm_running:
            threading.Thread(target=start_alarm, daemon=True).start()

        # Notifications
        threading.Thread(target=send_email, args=(alert_msg, severity), daemon=True).start()
        threading.Thread(target=send_whatsapp, args=(alert_msg, severity), daemon=True).start()

camera.release()
