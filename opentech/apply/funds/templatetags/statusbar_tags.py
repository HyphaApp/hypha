from collections import defaultdict
from django import template

register = template.Library()


def find_last_visible_phase(phases, user, current_phase):
    last_phase = current_phase
    while not last_phase.permissions.can_view(user):
        last_phase = phases[last_phase.step - 1][0]
    return last_phase


@register.inclusion_tag('funds/includes/status_bar.html')
def status_bar(workflow, current_phase, user, css_class='', same_stage=False):

    all_phases = defaultdict(list)
    for phase in list(workflow.values()):
        all_phases[phase.step].append(phase)

    # Grab the first phase for each step - visible only, the display phase
    phases = [
        phase for phase, *_ in all_phases.values()
        if phase.permissions.can_view(user)
        and (not same_stage or phase.stage == current_phase.stage)
    ]

    if not current_phase.permissions.can_view(user):
        current_phase = find_last_visible_phase(all_phases, user, current_phase)

    # Current step not shown for user, move current phase to last good location
    elif not all_phases[current_phase.step][0].permissions.can_view(user):
        new_phase_list = []
        for phase in reversed(phases):
            if phase.step <= current_phase.step and current_phase not in new_phase_list:
                next_phase = current_phase
            else:
                next_phase = phase
            new_phase_list = [next_phase, *new_phase_list]
        phases = new_phase_list

    return {
        'phases': phases,
        'current_phase': current_phase,
        'class': css_class,
        'public': user.is_applicant,
    }
