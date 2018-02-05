from wagtail.wagtailcore.blocks import StaticBlock

from opentech.public.utils.blocks import StoryBlock


class ProjectsBlock(StaticBlock):
    class Meta:
        icon = 'grip'
        label = 'List of Projects funded'
        admin_text = f'{label}: Will include the list of projects under this fund.'
        template = 'public_funds/blocks/related_projects.html'


class ReviewersBlock(StaticBlock):
    class Meta:
        icon = 'grip'
        label = 'List of fund Reviewers'
        admin_text = f'{label}: Will include the list of reviewers for this fund.'
        template = 'public_funds/blocks/related_reviewers.html'


class FundBlock(StoryBlock):
    project_list = ProjectsBlock()
    reviewer_list = ReviewersBlock()


class LabBlock(StoryBlock):
    reviewer_list = ReviewersBlock()
