from django import forms
from django.shortcuts import render
from django.template.response import TemplateResponse

from .workflow import SingleStage, DoubleStage


workflows = [SingleStage, DoubleStage]

logs = []

submission = {}


class BasicSubmissionForm(forms.Form):
    who_are_you = forms.CharField()


def demo_workflow(request, wf_id):
    wf = int(wf_id)
    workflow_class = workflows[wf-1]
    workflow = workflow_class([BasicSubmissionForm] * wf)

    current_phase = request.POST.get('current')
    current = workflow.current(current_phase)

    if request.POST:
        if current.stage.name not in submission:
            submitted_form = current.stage.form(request.POST)
            if submitted_form.is_valid():
                submission[current.stage.name] = submitted_form
                phase = current
                logs.append(
                    f'{phase.stage}: Form was submitted'
                )
                form = None
            else:
                form = submitted_form
        else:
            phase = workflow.process(current_phase, request.POST['action'])
            logs.append(
                f'{current.stage}: {current.name} was updated to {phase.stage}: {phase.name}'
            )
    else:
        phase = current
        logs.clear()
        submission.clear()

    if phase.stage.name not in submission:
        form = phase.stage.form
    else:
        form = None

    context = {
        'workflow': workflow,
        'phase': phase,
        'logs': logs,
        'data': submission,
        'form': form,
    }
    return TemplateResponse(request, 'apply/demo_workflow.html', context)


