from normalize import normalize

def check_normalize() -> None:
    # Empty and whitespace cases are covered.
    assert normalize("") == ""
