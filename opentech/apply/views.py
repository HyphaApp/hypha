from django.forms import Form
from django.shortcuts import render
from django.template.response import TemplateResponse

from .workflow import SingleStage, DoubleStage


workflows = [SingleStage, DoubleStage]

logs = []

def demo_workflow(request, wf_id):
    wf = int(wf_id)
    workflow_class = workflows[wf-1]
    workflow = workflow_class([Form()] * wf)

    current_phase = request.POST.get('current')
    if request.POST:
        current = workflow.current(current_phase)
        phase = workflow.process(current_phase, request.POST['action'])
        logs.append(
            f'{current.stage}: {current.name} was updated to {phase.stage}: {phase.name}'
        )
    else:
        phase = workflow.current(current_phase)
        logs.clear()

    context = {
        'workflow': workflow,
        'phase': phase,
        'logs': logs,
    }
    return TemplateResponse(request, 'apply/demo_workflow.html', context)


