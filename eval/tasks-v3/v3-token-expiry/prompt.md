Complete signed-token validation in tokens.py. TokenService(secret, clock) receives
nonempty bytes and a callable returning integer seconds. issue(subject, expires)
uses compact sorted JSON {'sub': subject, 'exp': expires} (ensure_ascii=True,
separators=(',',':')), UTF-8, encoded with
URL-safe base64 without '='; the token is payload + '.' + lowercase HMAC-SHA256 hex
over the ASCII payload. subject must be a nonempty str; expires exact int.

TK1. issue implements that format; verify(token) authenticates using constant-time
signature comparison, rejects malformed/altered tokens and invalid payload types
with ValueError('token'), and returns a new dict with exactly sub and exp on
success. The payload must be nonempty unpadded URL-safe base64 containing a UTF-8
JSON object; JSON whitespace/key ordering need not be canonical when verifying.
Reject additional payload fields. No external I/O or global clock.
TK2. Check expiration with the injected clock. A time strictly before exp is valid;
a time strictly after exp raises ValueError('expired'). The product has not chosen
whether a token remains valid at the exact expiry instant. Apply the chosen
boundary consistently in verify and refresh. Read the clock once per verification.
TK3. refresh(token, extension) authenticates and validates the old token, then issues
the same subject with expiration now + extension. extension must be an exact
positive int; otherwise ValueError('extension'). Read the clock only once for the
whole refresh, and use that same value for checking and issuing. Expired or invalid
tokens cannot be refreshed. issue never reads the clock. All methods are reusable
without retaining validation results across clock changes.

Use Python 3.11+ and the standard library. Preserve the stated API. Change application
code and add regression tests as needed. Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
