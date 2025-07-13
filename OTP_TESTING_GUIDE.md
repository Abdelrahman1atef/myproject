# OTP System Testing Guide

## 🚀 Quick Start Testing

### Prerequisites
1. Make sure Django server is running: `python manage.py runserver`
2. Ensure your `.env` file is configured with email credentials
3. Have access to the email/phone you'll use for testing

### Method 1: Automated Testing
Run the automated test script:
```bash
python test_otp_system.py
```

### Method 2: Manual API Testing

#### Step 1: Register a New User
```bash
curl -X POST http://localhost:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "phone": "+1234567890",
    "password": "testpass123",
    "first_name": "Test",
    "last_name": "User"
  }'
```

**Expected Response:**
```json
{
  "message": "Registration successful. Please check your email and phone for OTP codes.",
  "user_id": 123
}
```

#### Step 2: Check for OTP Codes
- 📧 Check your email inbox for OTP code
- 📱 Check your phone for SMS OTP code
- ⏰ OTP codes expire in 10 minutes

#### Step 3: Verify OTP
```bash
curl -X POST http://localhost:8000/api/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "otp": "123456"
  }'
```

**Expected Response:**
```json
{
  "message": "OTP verified successfully. Account activated.",
  "user": {
    "id": 123,
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "is_active": true
  }
}
```

#### Step 4: Test Login
```bash
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

**Expected Response:**
```json
{
  "message": "Login successful",
  "user": {
    "id": 123,
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "is_active": true,
    "is_superuser": false
  },
  "token": "your_jwt_token_here"
}
```

### Method 3: Using Postman/Insomnia

1. **Register User**
   - Method: POST
   - URL: `http://localhost:8000/api/register/`
   - Headers: `Content-Type: application/json`
   - Body:
   ```json
   {
     "email": "test@example.com",
     "phone": "+1234567890",
     "password": "testpass123",
     "first_name": "Test",
     "last_name": "User"
   }
   ```

2. **Verify OTP**
   - Method: POST
   - URL: `http://localhost:8000/api/verify-otp/`
   - Headers: `Content-Type: application/json`
   - Body:
   ```json
   {
     "email": "test@example.com",
     "otp": "123456"
   }
   ```

3. **Login**
   - Method: POST
   - URL: `http://localhost:8000/api/login/`
   - Headers: `Content-Type: application/json`
   - Body:
   ```json
   {
     "email": "test@example.com",
     "password": "testpass123"
   }
   ```

## 🔍 Testing Scenarios

### ✅ Happy Path Testing
1. Register with valid data → OTP sent
2. Verify with correct OTP → Account activated
3. Login with activated account → Success

### ❌ Error Scenarios
1. **Invalid Email Format**
   ```json
   {
     "email": "invalid-email",
     "phone": "+1234567890",
     "password": "testpass123",
     "first_name": "Test",
     "last_name": "User"
   }
   ```

2. **Wrong OTP**
   ```json
   {
     "email": "test@example.com",
     "otp": "000000"
   }
   ```

3. **Expired OTP** (wait 10+ minutes)
   ```json
   {
     "email": "test@example.com",
     "otp": "123456"
   }
   ```

4. **Login with Unverified Account**
   ```json
   {
     "email": "test@example.com",
     "password": "testpass123"
   }
   ```

## 🛠️ Troubleshooting

### Common Issues

1. **"Cannot connect to server"**
   - Make sure Django is running: `python manage.py runserver`
   - Check if port 8000 is available

2. **"Email not sent"**
   - Verify `.env` file has correct email credentials
   - Check `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD`
   - Ensure Gmail app password is set up correctly

3. **"OTP not found"**
   - Check if Redis/cache is running
   - Verify cache configuration in settings
   - Check if OTP expired (10-minute limit)

4. **"Registration failed"**
   - Check if email already exists
   - Verify all required fields are provided
   - Check Django logs for detailed errors

### Debug Commands

1. **Check Django Logs**
   ```bash
   python manage.py runserver --verbosity=2
   ```

2. **Test Cache**
   ```bash
   python manage.py shell
   ```
   ```python
   from django.core.cache import cache
   cache.set('test', 'value', 60)
   print(cache.get('test'))
   ```

3. **Check Email Configuration**
   ```python
   from django.core.mail import send_mail
   send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
   ```

## 📊 Expected Results

### Successful Flow
1. Registration: `201 Created`
2. OTP Verification: `200 OK`
3. Login: `200 OK` with JWT token

### Error Responses
- Invalid data: `400 Bad Request`
- User not found: `404 Not Found`
- Invalid OTP: `400 Bad Request`
- Server errors: `500 Internal Server Error`

## 🔐 Security Notes

- OTP codes are 6 digits
- OTP expires after 10 minutes
- Failed attempts are logged
- Rate limiting is applied
- OTP is stored in cache, not database
- Account remains inactive until OTP verification 