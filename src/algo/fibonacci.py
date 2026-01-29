def fib(n: int) -> int:
    """
    Возвращает n-ое число Фибоначчи.

    Args:
        n (int): Номер числа Фибоначчи.

    Returns:
        int: n-ое число Фибоначчи.
    """
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fib(n - 1) + fib(n - 2)
