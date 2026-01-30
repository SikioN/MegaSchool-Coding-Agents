import re

def validate_email(email: str) -> bool:
    """
    Validates if the provided email is valid using a regular expression.

    Args:
        email (str): The email address to validate.

    Returns:
        bool: True if the email is valid, False otherwise.
    """
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(email_regex, email) is not None

if __name__ == "__main__":
    print(validate_email("test@example.com"))  # Expected: True
    print(validate_email("invalid-email"))     # Expected: False
