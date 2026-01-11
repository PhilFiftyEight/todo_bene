from dataclasses import dataclass, field
from uuid import UUID, uuid4

@dataclass
class User:
    name: str
    email: str
    uuid: UUID = field(default_factory=uuid4)
