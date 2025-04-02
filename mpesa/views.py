from django.contrib import messages
from django.shortcuts import render, redirect
from dotenv import load_dotenv
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .utils import generate_access_token, initiate_stk_push
from .models import MpesaTransaction
import os
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Create your views here.

class MpesaPaymentView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            # Load credentials
            consumer_key = os.getenv("MPESA_CONSUMER_KEY", "your_consumer_key")
            consumer_secret = os.getenv("MPESA_CONSUMER_SECRET", "your_consumer_secret")
            business_short_code = os.getenv("MPESA_BUSINESS_SHORT_CODE", "your_short_code")
            partyB_till_number = os.getenv("MPESA_TILL_NUMBER", "your_till_number")
            passkey = os.getenv("MPESA_PASSKEY", "your_passkey")
            
            # Callback URL
            callback_url = os.getenv("MPESA_CALLBACK_URL", "your_mpesa_callback_url")

            # Get amount from session instead of request data
            amount_str = request.session.get("cart_total_amount")

            # Convert the decimal string amount to an integer
            # First, convert to float, then to integer by removing the decimal part
            # amount = int(float(amount_str))

            """ Account Order Number/Details Debugging """
            # logger.info(f"Request Data: {request.data}")
            # logger.info(f"Session Data: {request.session.items()}")  # Log all session data

            # Parse request data
            amount = request.data.get("amount")
            phone_number = request.data.get("phone_number")
            account_reference = request.data.get("account_reference", "DEFAULT_REF")
            transaction_desc = request.data.get("transaction_desc", "Payment Description")

            """ Account Order Number/Details Debugging """
            # logger.info(f"Account Reference: {account_reference}")
            # logger.info(f"Transaction Description: {transaction_desc}")

            # Validate phone number
            if not phone_number:
                messages.error(request, 'Phone number is required to proceed with the transaction.')
                return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate amount
            if not amount:
                messages.error(request, 'Unable to process transaction due to missing amount.')
                return Response({"error": "Unable to process transaction due to missing amount"}, status=status.HTTP_400_BAD_REQUEST)

            # Generate access token
            access_token = generate_access_token(consumer_key, consumer_secret)

            # Initiate STK push
            try:
                response = initiate_stk_push(
                    business_short_code,
                    passkey,
                    access_token,
                    amount,
                    partyB_till_number,
                    phone_number,
                    account_reference,
                    transaction_desc,
                    callback_url,
                )
                
                # Debugging: Log the response
                logger.info(f"STK Push Response: {response}")
            except Exception as stk_push_error:
                logger.error(f"STK Push Error: {stk_push_error}")
                messages.error(request, 'Failed to initiate STK push.')
                return Response({"error": str(stk_push_error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Save transaction
            transaction = MpesaTransaction.objects.create(
                transaction_id=response.get("CheckoutRequestID", "UNKNOWN"),
                phone_number=phone_number,
                amount=amount,
                account_reference=account_reference,
                transaction_desc=transaction_desc,
                status="processing",
            )

            # Store the transaction ID in the session for later verification
            request.session['mpesa_transaction_id'] = transaction.transaction_id

            # Store the phone number in the session for the invoice
            request.session['phone_number'] = transaction.phone_number

            # Add success message
            messages.success(request, "Transaction initiated successfully.")

            # Return success response
            return Response({
                "status": "success",
                "message": "Transaction initiated successfully",
                "transaction_id": transaction.transaction_id
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            # Log the error with full traceback
            logger.error(f"Mpesa Payment Error: {str(e)}", exc_info=True)
            
            # Add error message
            messages.error(request, 'Transaction failed. Please try again later.')
            
            # Return error response
            return Response({
                "status": "error",
                "message": "Transaction failed. Please try again later.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MpesaCallbackView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            # Log the entire callback data for debugging
            logger.info(f"Received M-Pesa Callback: {request.data}")
            
            # Extract callback data
            callback_data = request.data.get('Body', {}).get('stkCallback', {})
            
            # Check result code
            result_code = callback_data.get('ResultCode')
            result_desc = callback_data.get('ResultDesc')
            
            # Find the corresponding transaction
            checkout_request_id = callback_data.get('CheckoutRequestID')
            merchant_request_id = callback_data.get('MerchantRequestID')
            
            # Find transaction by CheckoutRequestID
            transaction = MpesaTransaction.objects.filter(
                transaction_id=checkout_request_id
            ).first()
            
            if not transaction:
                logger.warning(f"No transaction found for CheckoutRequestID: {checkout_request_id}")
                return Response({"status": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # Update transaction status
            if result_code == 0:
                # Successful transaction
                transaction.status = "paid"
                
                # Extract additional metadata
                metadata = callback_data.get('CallbackMetadata', {}).get('Item', [])
                
                # Create a safer dictionary from metadata items
                metadata_dict = {}
                for item in metadata:
                    if 'Name' in item and 'Value' in item:
                        metadata_dict[item['Name']] = item['Value']
                
                # Update transaction with additional details
                if 'Amount' in metadata_dict:
                    transaction.amount = metadata_dict['Amount']
                if 'MpesaReceiptNumber' in metadata_dict:
                    transaction.mpesa_receipt_number = metadata_dict['MpesaReceiptNumber']
                if 'TransactionDate' in metadata_dict:
                    transaction.transaction_date = metadata_dict['TransactionDate']
                if 'PhoneNumber' in metadata_dict:
                    transaction.phone_number = metadata_dict['PhoneNumber']
                
                logger.info(f"Successful transaction: {transaction.transaction_id}")
            else:
                # Failed transaction
                transaction.status = "failed"
                logger.warning(f"Failed transaction: {result_desc}")
            
            # Save the updated transaction
            transaction.callback_data = request.data
            transaction.save()
            
            return Response({"status": "Callback processed successfully"}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error processing M-Pesa callback: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Mpesa Payment via API
class APIMpesaPaymentView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            # Load credentials
            consumer_key = os.getenv("MPESA_CONSUMER_KEY", "your_consumer_key")
            consumer_secret = os.getenv("MPESA_CONSUMER_SECRET", "your_consumer_secret")
            business_short_code = os.getenv("MPESA_BUSINESS_SHORT_CODE", "your_short_code")
            passkey = os.getenv("MPESA_PASSKEY", "your_passkey")
            
            # Change the callback URL
            callback_url = "https://2823-41-139-160-178.ngrok-free.app/mpesa-callback/"

            # Parse request data
            amount = request.data.get("amount")
            phone_number = request.data.get("phone_number")
            account_reference = request.data.get("account_reference", "DEFAULT_REF")
            transaction_desc = request.data.get("transaction_desc", "Payment Description")

            if not amount or not phone_number:
                return Response({"error": "Amount and phone number are required"}, status=status.HTTP_400_BAD_REQUEST)

            # Generate access token
            access_token = generate_access_token(consumer_key, consumer_secret)

            # Initiate STK push
            response = initiate_stk_push(
                business_short_code,
                passkey,
                access_token,
                amount,
                phone_number,
                account_reference,
                transaction_desc,
                callback_url,
            )

            # Save transaction
            MpesaTransaction.objects.create(
                transaction_id=response.get("CheckoutRequestID", "UNKNOWN"),
                phone_number=phone_number,
                amount=amount,
                account_reference=account_reference,
                transaction_desc=transaction_desc,
                status="processing",
            )

            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)