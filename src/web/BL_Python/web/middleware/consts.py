CORRELATION_ID_HEADER = "X-Correlation-Id"
REQUEST_COOKIE_HEADER = "Cookie"
RESPONSE_COOKIE_HEADER = "Set-Cookie"
CORS_ACCESS_CONTROL_ALLOW_ORIGIN_HEADER = "Access-Control-Allow-Origin"
CORS_ACCESS_CONTROL_ALLOW_CREDENTIALS_HEADER = "Access-Control-Allow-Credentials"
CORS_ACCESS_CONTROL_ALLOW_METHODS_HEADER = "Access-Control-Allow-Methods"
CONTENT_SECURITY_POLICY_HEADER = "Content-Security-Policy"
ORIGIN_HEADER = "Origin"
HOST_HEADER = "Host"

INCOMING_REQUEST_MESSAGE = "Incoming request:\n\
    %s %s\n\
    Host: %s\n\
    Remote address: %s\n\
    Remote user: %s"

OUTGOING_RESPONSE_MESSAGE = f"Outgoing response:\n\
   Status code: %s\n\
   Status: %s"
