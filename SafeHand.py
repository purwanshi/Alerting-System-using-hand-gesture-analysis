import cv2
from cvzone.HandTrackingModule import HandDetector
from playsound import playsound
import threading #for smoothness
from twilio.rest import Client
import webbrowser
import requests

# Twilio setup
account_sid = 'ACCOUNT_SID'
auth_token = 'AUTH_TOKEN'
twilio_number = 'TWILIO_NUMBER'

client = Client(account_sid, auth_token)

# Emergency contact lists
phone_numbers = ['+91**********']
call_numbers = ['+91**********']

# Initialize Hand Detector
hd = HandDetector(detectionCon=0.8, maxHands=1)
cap = cv2.VideoCapture(0)

# Flags to prevent repeated triggers
alarm_triggered = False
sms_sent = False
call_made = False

# Accurate Location Fetching using ipinfo.io
def get_location():
    try:
        response = requests.get('https://ipinfo.io/json')
        data = response.json()
        if 'loc' in data:
            loc = data['loc'].split(',')
            return [float(loc[0]), float(loc[1])]
        else:
            return None
    except:
        return None

# SMS sending function
def send_emergency_sms(location=None):
    for number in phone_numbers:
        message_body = "🚨 Emergency detected! Please respond immediately."
        if location:
            message_body += f" Location: https://www.google.com/maps?q={location[0]},{location[1]}"
        message = client.messages.create(
            body=message_body,
            from_=twilio_number,
            to=number
        )
        print(f"SMS sent to {number}: {message.sid}")

# Phone call function
def make_emergency_call():
    for number in call_numbers:
        call = client.calls.create(
            twiml='<Response><Say>Emergency detected. Please check immediately!</Say></Response>',
            from_=twilio_number,
            to=number
        )
        print(f"Call made to {number}: {call.sid}")

# Open location in browser
def open_location_in_browser(location):
    url = f"https://www.google.com/maps?q={location[0]},{location[1]}"
    webbrowser.open(url)

# Main loop
while True:
    status, photo = cap.read()
    if not status:
        break

    hands, img = hd.findHands(photo)
    if hands:
        hand = hands[0]
        fingerup = hd.fingersUp(hand)
        print("Fingers Up:", fingerup)

        # Open palm triggers alarm, location, and SMS
        if fingerup == [1, 1, 1, 1, 1] and not alarm_triggered:
            threading.Thread(target=playsound, args=('alarm.mp3',), daemon=True).start()
            loc = get_location()
            if loc:
                print(f"📍 Location: {loc}")
                send_emergency_sms(loc)
                open_location_in_browser(loc)
            else:
                print("Location unavailable")
            alarm_triggered = True

        # Thumb up triggers SMS
        elif fingerup == [0, 1, 0, 0, 0] and not sms_sent:
            print("📨 Gesture Detected — Sending SMS")
            send_emergency_sms()
            sms_sent = True

        # Index and pinky up triggers call
        elif fingerup == [1, 0, 0, 0, 1] and not call_made:
            print("📞 Gesture Detected — Making Call")
            make_emergency_call()
            call_made = True

    # Show video feed
    cv2.imshow("Emergency Detection System", photo)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
