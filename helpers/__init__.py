from base64 import b64encode
from typing import List, Union

from mailjet_rest import Client
from requests import post

from config import API_KEY, from_email, API_SECRET, RECAPTCHA_SECRET_KEY, backend_url


def convert_to_slug(name):
    return name.replace(' ', '-').lower()


def without_keys(d, keys: List[str]) -> dict:
    return {x: d[x] for x in d if x not in keys}


def send_email(data: dict, sender=from_email,
               to=None, filename=None, sender_name='Mangalibe', to_name=None):
    try:
        subject = data['subject']
        message = data['message']
        mailjet = Client(auth=(API_KEY, API_SECRET), version='v3.1')
        data = {
            'Messages': [
                {
                    "From": {
                        "Email": sender,
                        "Name": sender_name
                    },
                    "To": [
                        {
                            "Email": to,
                            "Name": to_name
                        }
                    ],
                    "Subject": subject,
                    "HTMLPart": message,
                    "CustomID": "ConfirmationEmail",
                }
            ]
        }
        if filename:
            with open(filename, 'rb') as binary_file:
                binary_file_data = binary_file.read()
                base64_encoded_data = b64encode(binary_file_data)
                base64_message = base64_encoded_data.decode('utf-8')
            binary_file.close()
            data.get('Messages')[0]['Attachments'] = [
                {
                    "ContentType": "application/pdf",
                    "Filename": filename.split('/')[-1],
                    "Base64Content": base64_message
                }
            ]
        result = mailjet.send.create(data=data)
    except Exception as e:
        print(e)
        return False, str(e)


def test_recaptcha(token) -> bool:
    captcha = token
    secret_key = RECAPTCHA_SECRET_KEY
    url = 'https://www.google.com/recaptcha/api/siteverify'
    headers = {
        'Content-type': 'application/x-www-form-urlencoded'
    }
    payload = {
        'secret': secret_key,
        'response': captcha
    }
    try:
        response = post(url,
                        headers=headers, data=payload, timeout=5)
        if response.status_code != 200:
            return False
        final_response = response.json()
        if not final_response['success'] or final_response['score'] < 0.5:
            return False
        return True
    except Exception as e:
        return False


def get_image_from_cart(cart_item: Union['CartItem', dict]):
    from models.user import CartItem
    if type(cart_item) != CartItem:
        cart_item = CartItem(**cart_item)
    if cart_item.attributes:
        for attribute in cart_item.attributes:
            if attribute.get('image'):
                return f'{backend_url}/{attribute.get("image")}'
    return f'{backend_url}/{cart_item.product.image}'
