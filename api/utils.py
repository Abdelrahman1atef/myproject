from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db import connection
from django.http import JsonResponse, Http404
import requests
from django.conf import settings
import json
from google.oauth2 import service_account
from google.auth.transport.requests import Request

import re
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
import random
import string


def custom_exception_handler(exc, context):

    # Call DRF's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Custom message to be shown to the user
        user_message = _("An error occurred.")

        # Handle ValidationError
        if isinstance(exc, ValidationError):
            errors = response.data

            # If the error is a dictionary (field-specific)
            if isinstance(errors, dict):
                # Check if it has nested errors (like email: [error], phone: [error])
                field_errors = []

                for key, value in errors.items():
                    if isinstance(value, list):
                        field_errors.extend(value)
                    else:
                        field_errors.append(value)

                # Try to find a good user-facing message
                if 'email' in errors and 'phone' in errors:
                    user_message = _(
                        "The email or phone number you've entered is already registered. "
                        "Please try logging in or use different details to sign up."
                    )
                elif 'email' in errors:
                    user_message = _(
                        "This email is already taken. Please try a different one or log in."
                    )
                elif 'phone' in errors:
                    user_message = _(
                        "This phone number is already registered. Please use another or log in."
                    )
                elif field_errors:
                    user_message = str(field_errors[0])  # First message as fallback
                else:
                    user_message = _("Please fix the errors below.")
            else:
                # Non-field errors (e.g., non_field_errors)
                if isinstance(errors, list):
                    user_message = str(errors[0])
                else:
                    user_message = str(errors)

        # General exceptions (e.g., PermissionDenied, NotFound)
        else:
            detail = response.data.get('detail', _('An error occurred.'))
            user_message = str(detail)

        # Build final response
        custom_data = {
            "message": user_message,
            "status_code": response.status_code,
            "errors": response.data,  # Full original error object
        }

        response.data = custom_data

    return response

def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
            if row[0] != 1:
                raise Exception("Database check failed")
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Server or DB down: {str(e)}'
        }, status=503)

    return JsonResponse({
        'status': 'ok',
        'message': 'Server and DB are running'
    })

def get_firebase_access_token():
    credentials = service_account.Credentials.from_service_account_file(
        settings.FIREBASE_CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/firebase.messaging']
    )
    credentials.refresh(Request())
    return credentials.token

def send_fcm_notification_v1(token, title, body, data=None):
    access_token = get_firebase_access_token()
    url = f"https://fcm.googleapis.com/v1/projects/{settings.FIREBASE_PROJECT_ID}/messages:send"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; UTF-8",
    }
    # Convert all data values to strings
    if data:
        data = {k: str(v) for k, v in data.items()}
    message = {
        "message": {
            "token": token,
            "notification": {
                "title": title,
                "body": body,
            },
            "data": data or {}
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(message))
    print("FCM response:", response.status_code, response.text)
    return response.json()

def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(email, otp_code):
    """Send OTP code to user's email"""
    subject = 'Email Verification OTP'
    message = f'''
    Your email verification code is: {otp_code}
    
    This code will expire in {settings.OTP_EXPIRY_MINUTES} minutes.
    
    If you didn't request this code, please ignore this email.
    
    Best regards,
    Your Pharmacy Team
    '''
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def validate_phone_number(phone):
    """Validate phone number format"""
    # Remove any non-digit characters
    phone_clean = re.sub(r'\D', '', phone)
    
    # Check if it's a valid phone number (basic validation)
    # This can be customized based on your country's phone number format
    if len(phone_clean) < 10 or len(phone_clean) > 15:
        return False, "Phone number must be between 10 and 15 digits"
    
    # Check if it starts with a valid country code or local number
    # This is a basic check - you might want to use a library like phonenumbers
    if not phone_clean.startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
        return False, "Invalid phone number format"
    
    return True, phone_clean

def create_otp_cache_key(email):
    """Create cache key for OTP"""
    return f"otp_{email}"

def create_otp_record(email):
    """Create and store OTP in cache (not database)"""
    # Generate OTP
    otp_code = generate_otp(settings.OTP_LENGTH)
    
    # Store in cache with expiration
    cache_key = create_otp_cache_key(email)
    cache_timeout = settings.OTP_EXPIRY_MINUTES * 60  # Convert to seconds
    
    # Store OTP in cache
    cache.set(cache_key, otp_code, cache_timeout)
    
    # Also store a flag to prevent multiple OTPs for same email
    rate_limit_key = f"otp_rate_limit_{email}"
    cache.set(rate_limit_key, True, 60)  # 1 minute rate limit
    
    return {
        'email': email,
        'otp_code': otp_code,
        'expires_at': timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
    }

def verify_otp(email, otp_code):
    """Verify OTP code from cache"""
    cache_key = create_otp_cache_key(email)
    stored_otp = cache.get(cache_key)
    
    if not stored_otp:
        return False, "OTP has expired or doesn't exist"
    
    if stored_otp != otp_code:
        return False, "Invalid OTP code"
    
    # Remove OTP from cache after successful verification
    cache.delete(cache_key)
    
    return True, "OTP verified successfully"

def is_otp_rate_limited(email):
    """Check if email is rate limited for OTP requests"""
    rate_limit_key = f"otp_rate_limit_{email}"
    return cache.get(rate_limit_key) is not None

def cleanup_expired_otps():
    """Cleanup function for expired OTPs (cache handles this automatically)"""
    # Cache automatically handles expiration, so this is just a placeholder
    # You can add additional cleanup logic here if needed
    pass

def create_user_registration_cache_key(email):
    """Create cache key for storing user registration data"""
    return f"user_registration_{email}"

def store_user_registration_data(email, user_data):
    """Store user registration data temporarily in cache"""
    cache_key = create_user_registration_cache_key(email)
    cache_timeout = settings.OTP_EXPIRY_MINUTES * 60  # Same as OTP expiry
    cache.set(cache_key, user_data, cache_timeout)
    return True

def get_user_registration_data(email):
    """Retrieve user registration data from cache"""
    cache_key = create_user_registration_cache_key(email)
    return cache.get(cache_key)

def clear_user_registration_data(email):
    """Clear user registration data from cache"""
    cache_key = create_user_registration_cache_key(email)
    cache.delete(cache_key)