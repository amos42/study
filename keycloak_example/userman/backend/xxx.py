import jwt
from jwt.exceptions import InvalidTokenError

# def decode_keycloak_jwt(token, public_key, audience=None, issuer=None):
#     """
#     Decodes and verifies a Keycloak JWT.

#     Args:
#         token (str): The Keycloak JWT to decode.
#         public_key (str): The public key (in PEM format) used to verify the token's signature.
#                             This can be obtained from Keycloak's OpenID Connect configuration.
#         audience (str, optional): The expected audience (client ID) of the token.
#                                     If provided, the 'aud' claim will be validated.
#         issuer (str, optional): The expected issuer URL of the token.
#                                 If provided, the 'iss' claim will be validated.

#     Returns:
#         dict: The decoded payload of the JWT if valid.

#     Raises:
#         InvalidTokenError: If the token is invalid or verification fails.
#     """
#     try:
#         options = {"verify_signature": True}
#         if audience:
#             options["require"] = ["aud"]
#             options["audience"] = audience
#         if issuer:
#             options["require"] = ["iss"]
#             options["issuer"] = issuer

#         decoded_token = jwt.decode(
#             token,
#             public_key,
#             algorithms=["RS256"],  # Keycloak typically uses RS256
#             options=options
#         )
#         return decoded_token
#     except InvalidTokenError as e:
#         raise InvalidTokenError(f"JWT decoding or verification failed: {e}")

# Example Usage:
# Replace with your actual Keycloak public key, token, audience, and issuer
# keycloak_public_key = """-----BEGIN PUBLIC KEY-----
# MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1rNBo2iV6yd/tWVDXOqW3qlrzwQ6v2UjTyZODOyTPISxFJwRWdxxWgPruPdXjE1CLEQKzOlgDuXVJdhZub6imW83fQQ0n2BCg3Du40rl7s2d2GFZcubFgJLqx9qwBV6w1JRVfrjBbwDylbb63YSF62IfIby7GoIX7TDhh8QFq3tikGeLbEQM0aT+AxQIt/V6/Ofgd0DJrINkOtFC8Tv4i/ST/K1X6G3ONEN1fiR5qrGFUNAhUIaH04cmN0Dz2LJS0WPTBlwSGadLStmqPVRA6F8YfTMkkN8tkppCZGK7DPKNxU12PC3Aj9IoHhlzRuceye5CFsFl7fgjhJ1wTTM/XwIDAQAB
# -----END PUBLIC KEY-----"""



# Example for HS256 (symmetric)
payload = {
    "sub": "user123",
    "name": "Example User",
    "exp": 1756789012  # Expiration time (Unix timestamp)
}
#secret = "OTP3HWboqvt9AymQEQtrYmXW4mXHVioh"
secret = "MIICmzCCAYMCBgGX96IgWDANBgkqhkiG9w0BAQsFADARMQ8wDQYDVQQDDAZtYXN0ZXIwHhcNMjUwNzExMDM1NjI2WhcNMzUwNzExMDM1ODA2WjARMQ8wDQYDVQQDDAZtYXN0ZXIwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDWs0GjaJXrJ3+1ZUNc6pbeqWvPBDq/ZSNPJk4M7JM8hLEUnBFZ3HFaA+u491eMTUIsRArM6WAO5dUl2Fm5vqKZbzd9BDSfYEKDcO7jSuXuzZ3YYVly5sWAkurH2rAFXrDUlFV+uMFvAPKVtvrdhIXrYh8hvLsaghftMOGHxAWre2KQZ4tsRAzRpP4DFAi39Xr85+B3QMmsg2Q60ULxO/iL9JP8rVfobc40Q3V+JHmqsYVQ0CFQhofThyY3QPPYslLRY9MGXBIZp0tK2ao9VEDoXxh9MySQ3y2SmkJkYrsM8o3FTXY8LcCP0igeGXNG5x7J7kIWwWXt+COEnXBNMz9fAgMBAAEwDQYJKoZIhvcNAQELBQADggEBAJHk2yFIlRZzqbUzhDlPXSD6xquYVKty+ikFdJG3BUdA5zTDBpKsLgQXwMpiqkXD3CyMkwXuB0DNotc4/wSUvC24jQNHVs+rP4DyIikz2Zhia4s+EDO3hFWby3SRVFCXTUWU2sk7Ojb1zBQsUxmrEGhWwWhJgU8CoGnuG6DfDgGCcgxLoTPxlwtGJNahwrejz8te05St6+obn++ZyNJFqfhulRb46n1X/2G8emN6SU1wLes/0bd67Vlwx3BkF/l6kjA6uPxFOKaN0y2u+ncRBIvA50kesG6gLJDSatQyy9N0C1QtRRYmNdjWxE/GpPPBe4A5Fq9BxHriVS4A72rBL5I="
keycloak_token = jwt.encode(payload, secret, algorithm="HS256")

print("Encoded JWT:", keycloak_token)
# Example for RS256 (asymmetric)
# private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"
# encoded_jwt_rs256 = jwt.encode(payload, private_key, algorithm="RS256")


#keycloak_token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJMNHI2aDVtNWxmdHdNSGREODY0T2tCN2UzTEwzLXp5Mzk4SHdpM1lyWXU0In0.eyJleHAiOjE3NTU4ODIxNzAsImlhdCI6MTc1NTg4MjExMCwianRpIjoib25sdGFjOjkyODRlZTg0LWJiZjEtMjEwMC04Mzk1LWY2YTQ1NGNmN2M2ZSIsImlzcyI6Imh0dHA6Ly9sb2NhbGhvc3Q6ODA4MC9yZWFsbXMvbWFzdGVyIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoic2VjdXJpdHktYWRtaW4tY29uc29sZSIsInNpZCI6IjMxZTM4NDM2LWU1MDItNDg5MC04OTg5LTM3ZGQ3OWY1M2U2NCIsInNjb3BlIjoib3BlbmlkIGVtYWlsIHByb2ZpbGUifQ.T19mTWRnxco2kvAyX8lC7A11wSHxc6arrxe13PUr8mMbQviVAPXkyLwBG6tpL58aHzOMP1g9EK54kcQP67d7o6GJtZEQZElFfyuJI7cArY9vuuQKi4J1hyRI3-OyX-vLSu0nH4rLA4A-1xx2SWn74Z1L7RdtIG9Pq_jXXpgpIlI-tqtwyWYWZvkpP4CZnQtfQPKPHD0IBiSm4yJVOiyyYW3177_lgYOIlTn0lHAu0RSUnIrzxl5PMmqiAberxWJUsGqTrWRxHs33tRZ1XAEYQYPy38yEoWhMGv7lOtMu2yyFc2gCT1fOfW7SNZQB-0NvEAWsZq4niW5J_i1o5xXKBQ"
# expected_audience = "test-be"
# expected_issuer = "http://localhost:8080/realms/master"

# try:
#     decoded_payload = decode_keycloak_jwt(
#         keycloak_token,
#         keycloak_public_key,
#         audience=expected_audience,
#         issuer=expected_issuer
#     )
#     print("Decoded JWT Payload:", decoded_payload)
# except InvalidTokenError as e:
#     print("Error:", e)




import base64
import json

def decode_jwt_part(token):
    header_b64, payload_b64, signature_b64 = token.split(".")

    def b64decode(data):
        padding = '=' * (-len(data) % 4)  # base64 padding 보정
        return base64.urlsafe_b64decode(data + padding)

    header = json.loads(b64decode(header_b64))
    payload = json.loads(b64decode(payload_b64))

    return header, payload, signature_b64

#token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjEyMywibmFtZSI6Iu2PrOqwgCIsImV4cCI6MTc0NjAyMDAwMH0.HX_Ls2NLMY3g9TzpvW2r9szGLpya3E5ZQJKZjOuf_7Y"

header, payload, signature_b64 = decode_jwt_part(keycloak_token)

print("Header:", header)
print("Payload:", payload)
print("signature_b64:", signature_b64)

