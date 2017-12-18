from django.shortcuts import render
from django.template.response import TemplateResponse

from .workflow import single_stage, two_stage


workflows = [single_stage, two_stage]


def demo_workflow(request, wf_id):
    workflow = workflows[int(wf_id)-1]
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


