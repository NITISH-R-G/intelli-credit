import os
import json
import base64
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import credentials, auth
from dotenv import load_dotenv

load_dotenv()

# Ensure the Firebase App is only initialized once
if not firebase_admin._apps:
    project_id = os.environ.get("FIREBASE_PROJECT_ID", "intelli-credit-ai-dhanu")
    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if cred_path and os.path.exists(cred_path):
        firebase_admin.initialize_app(credentials.Certificate(cred_path))
    else:
        # Initialize with project ID; relies on Application Default Credentials
        firebase_admin.initialize_app(options={"projectId": project_id})

security = HTTPBearer(auto_error=False)

_SKIP_VERIFY = os.environ.get("SKIP_FIREBASE_VERIFY", "false").lower() == "true"


def verify_firebase_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    FastAPI Dependency to intercept the Authorization header and verify the Firebase JWT.
    
    In local development you can set SKIP_FIREBASE_VERIFY=true in .env to bypass
    signature verification. This must NEVER be enabled in production.
    """
    # ── Local dev bypass (if no header or skip verify is on) ──────────────
    if _SKIP_VERIFY:
        if not credentials:
            return {"uid": "dev_user", "email": "dev@localhost"}
            
        token = credentials.credentials
        try:
            parts = token.split(".")
            if len(parts) == 3:
                payload_b64 = parts[1]
                payload_b64 += "=" * (-len(payload_b64) % 4)
                decoded = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))
                if "uid" not in decoded:
                    decoded["uid"] = decoded.get("user_id", decoded.get("sub", "dev_user"))
                return decoded
        except Exception:
            pass
        # Fallback: return a dev user stub
        return {"uid": "dev_user", "email": "dev@localhost"}

    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing authentication token. Please sign in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    token = credentials.credentials

    # ── Production: full Firebase JWT verification ─────────────────────────────────
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
