from rest_framework.authentication import TokenAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

class CustomTokenAuthentication(TokenAuthentication):
    keyword = ''  # نخليها فاضية علشان نرسل التوكن بدون كلمة "Token"

    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if not auth or auth[0] == b'':
            return None

        if len(auth) == 1:
            try:
                token = auth[0].decode()
            except UnicodeError:
                raise AuthenticationFailed('Invalid token header. Token string should not contain invalid characters.')
            return self.authenticate_credentials(token)
        else:
            raise AuthenticationFailed('Invalid token header. Token string should not contain spaces.')
