from django import template

register = template.Library()


@register.inclusion_tag('funds/includes/status_bar.html')
def status_bar(workflow, current_phase, user, css_class='', same_stage=False):

    phases = workflow.phases_for(user)

    if same_stage and not user.is_applicant:
        phases = [
            phase for phase in phases
            if phase.stage == current_phase.stage
        ]

    if not current_phase.permissions.can_view(user):
        current_phase = workflow.previous_visible(current_phase, user)

    # Current step not shown for user, move current phase to last good location
    elif not workflow.stepped_phases[current_phase.step][0].permissions.can_view(user):
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


@register.simple_tag()
def status_display(current_phase, phase, public):
    if phase.step == current_phase.step:
        if public:
            return current_phase.public_name
        else:
            return current_phase.display_name

    if phase.step > current_phase.step:
        if public:
            return phase.future_name_public
        else:
            return phase.future_name_staff

    if public:
        return phase.public_name
    else:
        return phase.display_name
