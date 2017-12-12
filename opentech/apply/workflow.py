class Workflow:
    def __init__(self, name, *stages):
        self.name = name
        if not stages:
            raise ValueError('Stages must be supplied')
        self.stages = stages


class Stage:
    def __init__(self, name):
        self.name = name
