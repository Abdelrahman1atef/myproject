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