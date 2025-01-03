from collections import defaultdict


class Workflow(dict):
    def __init__(self, name, admin_name, **data):
        self.name = name
        self.admin_name = admin_name
        super().__init__(**data)

    def __str__(self):
        return self.name

    @property
    def stages(self):
        stages = []
        for phase in self.values():
            if phase.stage not in stages:
                stages.append(phase.stage)
        return stages

    @property
    def stepped_phases(self):
        phases = defaultdict(list)
        for phase in list(self.values()):
            phases[phase.step].append(phase)
        return phases

    def phases_for(self, user=None):
        # Grab the first phase for each step - visible only, the display phase
        return [
            phase
            for phase, *_ in self.stepped_phases.values()
            if not user or phase.permissions.can_view(user)
        ]

    def previous_visible(self, current, user):
        """Find the latest phase that the user has view permissions for"""
        display_phase = self.stepped_phases[current.step][0]
        phases = self.phases_for()
        index = phases.index(display_phase)
        for phase in phases[index - 1 :: -1]:
            if phase.permissions.can_view(user):
                return phase
