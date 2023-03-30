from collections import defaultdict

from . import definitions
from .phase import Phase


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


def phase_data(phases):
    def unpack_phases(phases):
        for step, step_data in enumerate(phases):
            for name, phase_data in step_data.items():
                yield step, name, phase_data

    return {
        phase_name: Phase(phase_name, step=step, **phase_data)
        for step, phase_name, phase_data in unpack_phases(phases)
    }


# Workflow definition's
Request = Workflow(
    name='Request', admin_name='single', **phase_data(definitions.SingleStageDefinition)
)

RequestExternal = Workflow(
    name='Request with external review',
    admin_name='single_ext',
    **phase_data(definitions.SingleStageExternalDefinition)
)

RequestCommunity = Workflow(
    name='Request with community review',
    admin_name='single_com',
    **phase_data(definitions.SingleStageCommunityDefinition)
)

ConceptProposal = Workflow(
    name='Concept & Proposal',
    admin_name='double',
    **phase_data(definitions.DoubleStageDefinition)
)


# Dict of workflows by admin name. It provides and easy way to find a workflow
# definition assigned.
WORKFLOWS = {
    Request.admin_name: Request,
    RequestExternal.admin_name: RequestExternal,
    RequestCommunity.admin_name: RequestCommunity,
    ConceptProposal.admin_name: ConceptProposal,
}
