import requests
import base64
import json
from datetime import datetime
from django.conf import settings

# Mpesa credentials (add to settings)
MPESA_CONSUMER_KEY = getattr(settings, 'MPESA_CONSUMER_KEY', 'your_consumer_key')
MPESA_CONSUMER_SECRET = getattr(settings, 'MPESA_CONSUMER_SECRET', 'your_consumer_secret')
MPESA_SHORTCODE = getattr(settings, 'MPESA_SHORTCODE', 'your_shortcode')
MPESA_PASSKEY = getattr(settings, 'MPESA_PASSKEY', 'your_passkey')
MPESA_BASE_URL = 'https://sandbox.safaricom.co.ke'  # Use live URL for production

def get_mpesa_access_token():
    url = f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET))
    if response.status_code == 200:
        return response.json()['access_token']
    return None

def initiate_stk_push(phone_number, amount, account_reference, transaction_desc):
    access_token = get_mpesa_access_token()
    if not access_token:
        return {'error': 'Failed to get access token'}

    url = f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest"
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode((MPESA_SHORTCODE + MPESA_PASSKEY + timestamp).encode()).decode()

    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": "https://yourdomain.com/mpesa/callback",  # Replace with your callback URL
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc
    }

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()

def handle_mpesa_callback(data):
    from .models import Payment
    # Process callback data
    # Assuming data has stkCallback structure
    if 'stkCallback' in data:
        stk_callback = data['stkCallback']
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc')

        try:
            payment = Payment.objects.get(transaction_id=checkout_request_id)
            if result_code == 0:
                payment.status = 'completed'
            else:
                payment.status = 'failed'
            payment.save()
        except Payment.DoesNotExist:
            pass  # Log error if needed
