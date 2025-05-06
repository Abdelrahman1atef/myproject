from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

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