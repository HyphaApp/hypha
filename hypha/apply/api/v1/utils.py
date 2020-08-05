
def get_review_form_fields_for_stage(submission):
    forms = submission.get_from_parent('review_forms').all()
    index = submission.workflow.stages.index(submission.stage)
    try:
        return forms[index].form.form_fields
    except IndexError:
        return forms[0].form.form_fields
