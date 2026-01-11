from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    name: str
