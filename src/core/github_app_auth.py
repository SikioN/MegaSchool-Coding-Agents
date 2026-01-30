import time
import jwt
import requests
from src.core.config import Config

class GitHubAppAuth:
    """
    Handles authetication for GitHub Apps.
    1. Generates JWT from Private Key.
    2. Requests Installation Access Token using JWT.
    """
    
    @staticmethod
    def get_jwt() -> str:
        """
        Gnerates a JSON Web Token (JWT) using the private key.
        Valid for 10 minutes.
        """
        pem_key = Config.GITHUB_PRIVATE_KEY
        if not pem_key:
            raise ValueError("GITHUB_PRIVATE_KEY is not set")
            
        # If the key is passed as a single line with \n, fix it (though python-dotenv handles quoted multiline)
        # But `jwt.encode` expects bytes or str.
        
        now = int(time.time())
        payload = {
            # Issued at time
            'iat': now - 60,
            # JWT expiration time (10 min maximum)
            'exp': now + (10 * 60),
            # GitHub App's identifier
            'iss': Config.GITHUB_APP_ID
        }
        
        encoded_jwt = jwt.encode(payload, pem_key, algorithm='RS256')
        return encoded_jwt

    @staticmethod
    def get_installation_token(installation_id: int) -> str:
        """
        Obtains an access token for a specific installation of the App.
        """
        jwt_token = GitHubAppAuth.get_jwt()
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json"
        }
        
        url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        response = requests.post(url, headers=headers)
        
        if response.status_code != 201:
            raise Exception(f"Failed to get installation token: {response.text}")
            
        return response.json()["token"]
