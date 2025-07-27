import os
import requests

BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8000')


def send_message(text: str):
    resp = requests.post(f"{BASE_URL}/api/chatbot/message/", json={"message": text})
    print('Message status:', resp.status_code)
    try:
        print(resp.json())
    except Exception:
        print(resp.text)


def send_image(path: str):
    with open(path, 'rb') as f:
        resp = requests.post(f"{BASE_URL}/api/chatbot/image/", files={'image': f})
    print('Image status:', resp.status_code)
    try:
        print(resp.json())
    except Exception:
        print(resp.text)


if __name__ == '__main__':
    send_message("How do I cook plov?")
    # send_image('photo.jpg')

