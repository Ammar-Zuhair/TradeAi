import requests
import json

def send_push_notification(token, title, body, data=None):
    """
    Send a push notification using Expo Push API.
    """
    if not token:
        return None
    
    # Check if token is a valid Expo push token
    if not token.startswith('ExponentPushToken') and not token.startswith('ExpoPushToken'):
        print(f"⚠️ Invalid Expo Push Token: {token}")
        return None

    message = {
        "to": token,
        "sound": "default",
        "title": title,
        "body": body,
        "data": data or {}
    }

    try:
        response = requests.post(
            "https://exp.host/--/api/v2/push/send",
            json=message,
            headers={
                "Accept": "application/json",
                "Accept-encoding": "gzip, deflate",
                "Content-Type": "application/json"
            },
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error sending push notification: {e}")
        return None
