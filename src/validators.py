import re

def validate_email(email: str) -> bool:
    """
    Проверяет, является ли строка действительным адресом электронной почты.

    Args:
        email (str): Адрес электронной почты для проверки.

    Returns:
        bool: True, если адрес действителен, False в противном случае.
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None

if __name__ == "__main__":
    print(validate_email("test@example.com"))  # True
    print(validate_email("invalid-email"))     # False
