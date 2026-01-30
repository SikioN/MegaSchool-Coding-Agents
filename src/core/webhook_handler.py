import hmac
import hashlib
from fastapi import Request, HTTPException
from src.core.config import Config

class WebhookVerificator:
    """
    Validates the GitHub Webhook signature.
    """
    
    @staticmethod
    async def verify_signature(request: Request):
        secret = Config.GITHUB_WEBHOOK_SECRET
        if not secret:
            raise HTTPException(status_code=500, detail="Webhook Secret not configured")
            
        signature = request.headers.get("X-Hub-Signature-256")
        if not signature:
            raise HTTPException(status_code=401, detail="Missing X-Hub-Signature-256 header")
            
        # Get raw body
        body = await request.body()
        
        # Calculate HMAC
        hash_object = hmac.new(
            secret.encode("utf-8"), 
            msg=body, 
            digestmod=hashlib.sha256
        )
        expected_signature = "sha256=" + hash_object.hexdigest()
        
        if not hmac.compare_digest(expected_signature, signature):
             raise HTTPException(status_code=401, detail="Invalid signature")
