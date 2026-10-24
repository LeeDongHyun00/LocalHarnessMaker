from dataclasses import dataclass

@dataclass(frozen=True)
class Stamp:
    digest: str
    mtime: int

@dataclass
class Previous:
    dependencies: list[str]
    input_digests: dict[str, str]
    built_at: int


