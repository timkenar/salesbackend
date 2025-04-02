import requests
import base64
from datetime import datetime
from requests.auth import HTTPBasicAuth

def generate_access_token(consumer_key, consumer_secret):
    """
        Generate access token for M-Pesa API
    """
    """ Sandbox URL """
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    """ Production URL  """
    # url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    response = requests.get(url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    if response.status_code == 200:
        return response.json().get("access_token")
    raise Exception(f"Failed to generate access token: {response.text}")

def generate_password(business_short_code, passkey):
    """
        Generate base64 encoded password
        Combines: BusinessShortCode + Passkey + Timestamp
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password_string = f"{business_short_code}{passkey}{timestamp}"
    return base64.b64encode(password_string.encode()).decode(), timestamp

def initiate_stk_push(business_short_code, passkey, access_token, amount, partyB_till_number, phone_number, account_reference, transaction_desc, callback_url):
    """
        Initiate STK Push with precise parameters as per Daraja API specification
    """
    password, timestamp = generate_password(business_short_code, passkey)
    
    """ Sandbox URL """
    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

    """ Production URL  """
    # url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "BusinessShortCode": business_short_code,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerBuyGoodsOnline",  # Use this for BuyGoods
        "Amount": str(int(amount)),  # Whole numbers only
        "PartyA": phone_number,
        "PartyB": partyB_till_number,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": account_reference[:12],  # Max 12 characters
        "TransactionDesc": transaction_desc[:13]  # Max 13 characters
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()