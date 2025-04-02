import os
import requests
import base64
from datetime import datetime
from dotenv import load_dotenv

class MpesaSTKPushHandler:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Fetch credentials from environment
        self.consumer_key = os.getenv('MPESA_CONSUMER_KEY')
        self.consumer_secret = os.getenv('MPESA_CONSUMER_SECRET')
        self.business_short_code = os.getenv('MPESA_BUSINESS_SHORT_CODE', '174379')
        self.passkey = os.getenv('MPESA_PASSKEY')
        self.callback_url = os.getenv('MPESA_CALLBACK_URL')
    
    def generate_password(self):
        """
        Dynamically generate base64 encoded password
        Combines: BusinessShortCode + Passkey + Timestamp
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password_string = f"{self.business_short_code}{self.passkey}{timestamp}"
        return base64.b64encode(password_string.encode()).decode(), timestamp
    
    def get_access_token(self):
        """
        Generate access token for M-Pesa API
        """
        url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        try:
            response = requests.get(url, auth=(self.consumer_key, self.consumer_secret))
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json().get('access_token')
        except requests.RequestException as e:
            print(f"Error generating access token: {e}")
            return None
    
    def initiate_stk_push(self, amount, phone_number, account_reference="TestPay", transaction_desc="Test Payment"):
        """
        Initiate STK Push with dynamic parameters
        """
        # Generate dynamic password and timestamp
        password, timestamp = self.generate_password()
        
        # Get access token
        access_token = self.get_access_token()
        if not access_token:
            print("Failed to obtain access token")
            return None
        
        # Prepare request payload
        payload = {
            "BusinessShortCode": self.business_short_code,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": str(int(amount)),  # Ensure whole number
            "PartyA": phone_number,
            "PartyB": self.business_short_code,
            "PhoneNumber": phone_number,
            "CallBackURL": self.callback_url,
            "AccountReference": account_reference[:12],  # Max 12 characters
            "TransactionDesc": transaction_desc[:13]  # Max 13 characters
        }
        
        # Prepare headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Send STK Push request
        try:
            url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error initiating STK Push: {e}")
            return None

def main():
    # Example usage
    mpesa_handler = MpesaSTKPushHandler()
    
    # Initiate STK Push
    # Replace with your test phone number
    response = mpesa_handler.initiate_stk_push(
        amount=1,  # Amount in whole numbers
        phone_number="254708374149",  # Your test M-Pesa registered phone number
        account_reference="TestPay",
        transaction_desc="Test Payment"
    )
    
    # Print response
    if response:
        print("STK Push Initiated Successfully:")
        print(f"Merchant Request ID: {response.get('MerchantRequestID')}")
        print(f"Checkout Request ID: {response.get('CheckoutRequestID')}")
        print(f"Response Code: {response.get('ResponseCode')}")
        print(f"Response Description: {response.get('ResponseDescription')}")
    else:
        print("Failed to initiate STK Push")

if __name__ == "__main__":
    main()