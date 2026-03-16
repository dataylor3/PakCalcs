from dataclasses import dataclass
from typing import Tuple, Optional

@dataclass
class DesignMember:
    id: int
    member_name: str
    element_list: Tuple[int, ...]


    @classmethod
    def from_item(cls, key: str, payload: dict) -> "DesignMember":
        return cls(
            id=int(key),
            member_name=payload["member_name"],
            element_list=tuple(payload.get("element_list", [])),
        )

    @classmethod
    def build_many(cls, outer: dict[str, dict]) -> list["DesignMember"]:
        return [cls.from_item(k, v) for k, v in outer.items()]
