"""
Allow JWT via query string for HTML5 video elements (cannot send Authorization headers).
Use HTTPS in production; tokens may appear in server access logs.
"""
from rest_framework_simplejwt.authentication import JWTAuthentication


class JWTAccessQueryAuthentication(JWTAuthentication):
    """Authenticate using ?access=<jwt> when the Authorization header is absent."""

    def authenticate(self, request):
        header = super().authenticate(request)
        if header is not None:
            return header
        token = request.query_params.get('access')
        if not token:
            return None
        validated = self.get_validated_token(token)
        return self.get_user(validated), validated
