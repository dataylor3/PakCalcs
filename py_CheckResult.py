from dataclasses import dataclass
from typing import Literal
import forallpeople as si
si.environment("mystructural", top_level=True)


@dataclass(frozen=True)
class BeamCheckResult:
    mechanism: Literal[
        "Mx", "My", "V", "N",
        "Mx+My", "Mx+N", "My+N"
    ]
    load_case_ID: str
    load_case_name: str
    position: si.Physical               # e.g. metres along beam
    utilisation: float

    demands: dict[str, si.Physical]
    capacities: dict[str, si.Physical]
    reference: str | None = None
    #capacity: si.Physical
    #demand: si.Physical

    def __str__(self):
        return f"{self.load_case_ID} {self.load_case_name} {self.mechanism} at {self.position}: " \
               f"capacity {self.capacities}, demand {self.demands}, utilisation {self.utilisation:.2f}"

    def __repr__(self):
        return str(self)