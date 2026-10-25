class Document:
    def __init__(self, text: str, selections: list[tuple[int, int]]) -> None:
        self.text = text
        self.selections = list(selections)
    def apply(self, edits: list[tuple[int, int, str]]) -> None:
        for start, end, replacement in edits:
            self.text = self.text[:start] + replacement + self.text[end:]
    def undo(self) -> bool:
        return False
