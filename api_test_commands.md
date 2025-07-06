# API Test Commands

## Using curl to test your API endpoints

### 1. Test All Users (Admin Only)
```bash
curl -X GET "https://locust-eminent-urchin.ngrok-free.app/api/admin/users/" \
  -H "Authorization: Token 089b79813f1cf73cf305fceae78710ce4cf60835" \
  -H "Content-Type: application/json"
```

### 2. Test Specific User Details (Admin Only)
```bash
curl -X GET "https://locust-eminent-urchin.ngrok-free.app/api/admin/users/1/" \
  -H "Authorization: Token 089b79813f1cf73cf305fceae78710ce4cf60835" \
  -H "Content-Type: application/json"
```

### 3. Test Available Products
```bash
curl -X GET "https://locust-eminent-urchin.ngrok-free.app/api/products/see-our-products/" \
  -H "Authorization: Token 089b79813f1cf73cf305fceae78710ce4cf60835" \
  -H "Content-Type: application/json"
```

### 4. Test Best Sellers
```bash
curl -X GET "https://locust-eminent-urchin.ngrok-free.app/api/products/best-sellers/" \
  -H "Authorization: Token 089b79813f1cf73cf305fceae78710ce4cf60835" \
  -H "Content-Type: application/json"
```

### 5. Test User Profile
```bash
curl -X GET "https://locust-eminent-urchin.ngrok-free.app/api/me/" \
  -H "Authorization: Token 089b79813f1cf73cf305fceae78710ce4cf60835" \
  -H "Content-Type: application/json"
```

## Using Python requests

```python
import requests

BASE_URL = "https://locust-eminent-urchin.ngrok-free.app/api"
TOKEN = "089b79813f1cf73cf305fceae78710ce4cf60835"

headers = {
    'Authorization': f'Token {TOKEN}',
    'Content-Type': 'application/json'
}

# Test all users
response = requests.get(f"{BASE_URL}/admin/users/", headers=headers)
print(response.status_code)
print(response.json())
```

## Notes:

1. **Admin Endpoints**: `/admin/users/` and `/admin/users/<id>/` require admin privileges
2. **Token Authentication**: All endpoints require the Authorization header with your token
3. **Pagination**: Most endpoints support pagination with `?page=1`, `?page=2`, etc.
4. **Error Handling**: Check the status code - 200 means success, 403 means forbidden (not admin), 404 means not found

## Common Issues:

1. **403 Forbidden**: Make sure your user has admin privileges (`is_staff=True`)
2. **404 Not Found**: Check if the user ID exists
3. **401 Unauthorized**: Check if your token is valid and not expired 