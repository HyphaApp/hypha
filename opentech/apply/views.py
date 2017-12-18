from django.forms import Form
from django.shortcuts import render
from django.template.response import TemplateResponse

from .workflow import SingleStage, DoubleStage


workflows = [SingleStage, DoubleStage]


def demo_workflow(request, wf_id):
    wf = int(wf_id)
    workflow_class = workflows[wf-1]
    workflow = workflow_class([Form()] * wf)

    current_phase = request.POST.get('current')
    if request.POST:
        phase = workflow.process(current_phase, request.POST['action'])
    else:
        phase = workflow.current(current_phase)

    context = {
        'workflow': workflow,
        'phase': phase,
    }
    return TemplateResponse(request, 'apply/demo_workflow.html', context)


