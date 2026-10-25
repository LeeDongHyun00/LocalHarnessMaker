import base64
import hashlib
import hmac
import json
from collections.abc import Callable
class TokenService:
    def __init__(self, secret: bytes, clock: Callable[[], int]) -> None:
        self.secret, self.clock = secret, clock
    def issue(self, subject: str, expires: int) -> str:
        if not isinstance(subject, str) or not subject or type(expires) is not int:
            raise ValueError('token')
        raw = json.dumps({'sub':subject,'exp':expires}, sort_keys=True, separators=(',',':')).encode()
        payload = base64.urlsafe_b64encode(raw).decode().rstrip('=')
        return payload + '.' + hmac.new(self.secret, payload.encode(), hashlib.sha256).hexdigest()
    def verify(self, token: str) -> dict:
        payload = token.split('.')[0]
        return json.loads(base64.urlsafe_b64decode(payload + '=' * (-len(payload) % 4)))
    def refresh(self, token: str, extension: int) -> str:
        return self.issue(self.verify(token)['sub'], self.clock() + extension)
