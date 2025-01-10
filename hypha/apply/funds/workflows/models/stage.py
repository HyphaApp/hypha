class Stage:
    __slots__ = ("name", "has_external_review")

    def __init__(self, name: str, has_external_review: bool = False) -> None:
        self.name = name
        self.has_external_review = has_external_review

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Stage: {self.name}>"


# Stage instances
Request = Stage("Request")
RequestSame = Stage("RequestSame", True)
RequestExt = Stage("RequestExt", True)
RequestCom = Stage("RequestCom", True)
Concept = Stage("Concept")
Proposal = Stage("Proposal", True)
