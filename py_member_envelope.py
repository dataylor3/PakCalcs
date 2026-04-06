from py_CheckResult import BeamCheckResult



class MemberEnvelope:
    def __init__(self):
        self._results: list[BeamCheckResult] = []
        self._governing: BeamCheckResult | None = None

    def add(self, result: BeamCheckResult):
        self._results.append(result)

        if (
            self._governing is None
            or result.utilisation > self._governing.utilisation
        ):
            self._governing = result

    @property
    def governing(self) -> BeamCheckResult:
        if self._governing is None:
            raise ValueError("Envelope contains no results")
        return self._governing

    @property
    def results(self) -> list[BeamCheckResult]:
        return self._results