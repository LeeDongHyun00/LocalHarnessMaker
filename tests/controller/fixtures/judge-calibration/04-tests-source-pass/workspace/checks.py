from normalize import normalize

def check_normalize() -> None:
    assert normalize("") == ""
    assert normalize(" AbC ") == "abc"
