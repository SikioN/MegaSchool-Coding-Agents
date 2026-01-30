import re

def validate_email(email: str) -> bool:
    """Validate an email address using a regular expression.

    Args:
        email (str): The email address to validate.

    Returns:
        bool: True if the email is valid, False otherwise.
    """
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(regex, email) is not None

if __name__ == "__main__":
    # Test cases
    valid_email = "test@example.com"
    invalid_email = "invalid-email"

    print(f"Testing '{valid_email}': {validate_email(valid_email)}")
    print(f"Testing '{invalid_email}': {validate_email(invalid_email)}")
