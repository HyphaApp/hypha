from dataclasses import dataclass


@dataclass
class Stage:
    name: str
    has_external_review: bool = False

    def __str__(self):
        return self.name


Request = Stage('Request', False)

RequestExt = Stage('RequestExt', True)

RequestCom = Stage('RequestCom', True)

Concept = Stage('Concept', False)

Proposal = Stage('Proposal', True)
