def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("zero divisor")
    return a / b
