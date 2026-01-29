def fib(n: int) -> int:
    """
    Returns the n-th Fibonacci number.

    Args:
        n (int): The index of the Fibonacci number.

    Returns:
        int: The n-th Fibonacci number.
    
    Raises:
        ValueError: If n is negative.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    elif n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fib(n - 1) + fib(n - 2)
