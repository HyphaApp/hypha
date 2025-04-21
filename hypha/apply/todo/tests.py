from django.contrib.auth.models import Group
from django.test import TestCase

from hypha.apply.activity.tests.factories import ActivityFactory
from hypha.apply.determinations.tests.factories import DeterminationFactory
from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory
from hypha.apply.projects.reports.tests.factories import ReportFactory
from hypha.apply.projects.tests.factories import (
    InvoiceFactory,
    ProjectFactory,
)
from hypha.apply.review.tests.factories import ReviewFactory
from hypha.apply.users.roles import CONTRACTING_GROUP_NAME, STAFF_GROUP_NAME
from hypha.apply.users.tests.factories import ContractingFactory, StaffFactory
from hypha.apply.utils.testing.tests import BaseViewTestCase

from .models import Task
from .options import (
    COMMENT_TASK,
    DETERMINATION_DRAFT,
    INVOICE_REQUIRED_CHANGES,
    INVOICE_WAITING_APPROVAL,
    INVOICE_WAITING_PAID,
    PAF_REQUIRED_CHANGES,
    PAF_WAITING_APPROVAL,
    PAF_WAITING_ASSIGNEE,
    PROJECT_SUBMIT_PAF,
    PROJECT_WAITING_CONTRACT,
    PROJECT_WAITING_CONTRACT_DOCUMENT,
    PROJECT_WAITING_CONTRACT_REVIEW,
    PROJECT_WAITING_INVOICE,
    PROJECT_WAITING_PF,
    PROJECT_WAITING_SOW,
    REPORT_DUE,
    REVIEW_DRAFT,
    SUBMISSION_DRAFT,
)
from .views import (
    add_task_to_user,
    add_task_to_user_group,
    get_tasks_for_user,
    remove_tasks_for_user,
    remove_tasks_for_user_group,
    remove_tasks_of_related_obj,
    remove_tasks_of_related_obj_for_specific_code,
)


class TestTaskAPIs(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = StaffFactory()
        cls.project = ProjectFactory()

    def tearDown(self):
        Task.objects.all().delete()

    def test_add_task_to_user_api(self):
        tasks = Task.objects.all()
        self.assertEqual(tasks.count(), 0)

        add_task_to_user(
            code=PROJECT_WAITING_CONTRACT, user=self.user, related_obj=self.project
        )
        self.assertEqual(Task.objects.all().count(), 1)

    def test_add_task_to_user_group_api(self):
        self.assertEqual(Task.objects.all().count(), 0)

        add_task_to_user_group(
            code=PROJECT_WAITING_CONTRACT,
            user_group=Group.objects.filter(name=CONTRACTING_GROUP_NAME),
            related_obj=self.project,
        )
        self.assertEqual(Task.objects.all().count(), 1)

    def test_remove_task_for_user_api(self):
        add_task_to_user(
            code=PROJECT_WAITING_CONTRACT, user=self.user, related_obj=self.project
        )
        self.assertEqual(Task.objects.all().count(), 1)

        remove_tasks_for_user(
            code=PROJECT_WAITING_CONTRACT, user=self.user, related_obj=self.project
        )
        self.assertEqual(Task.objects.all().count(), 0)

    def test_remove_task_for_user_group_api(self):
        add_task_to_user_group(
            code=PROJECT_WAITING_CONTRACT,
            user_group=Group.objects.filter(name=CONTRACTING_GROUP_NAME),
            related_obj=self.project,
        )
        self.assertEqual(Task.objects.all().count(), 1)

        remove_tasks_for_user_group(
            code=PROJECT_WAITING_CONTRACT,
            user_group=Group.objects.filter(name=CONTRACTING_GROUP_NAME),
            related_obj=self.project,
        )
        self.assertEqual(Task.objects.all().count(), 0)

    def test_remove_all_task_of_related_obj(self):
        add_task_to_user(
            code=PROJECT_WAITING_CONTRACT, user=self.user, related_obj=self.project
        )
        add_task_to_user_group(
            code=PROJECT_WAITING_CONTRACT,
            user_group=Group.objects.filter(name=CONTRACTING_GROUP_NAME),
            related_obj=self.project,
        )
        self.assertEqual(Task.objects.all().count(), 2)

        remove_tasks_of_related_obj(related_obj=self.project)
        self.assertEqual(Task.objects.all().count(), 0)

    def test_remove_task_of_related_obj_with_code(self):
        add_task_to_user(
            code=PROJECT_WAITING_CONTRACT, user=self.user, related_obj=self.project
        )

        add_task_to_user(
            code=PROJECT_WAITING_INVOICE, user=self.user, related_obj=self.project
        )
        self.assertEqual(Task.objects.all().count(), 2)

        remove_tasks_of_related_obj_for_specific_code(
            code=PROJECT_WAITING_CONTRACT, related_obj=self.project
        )
        self.assertEqual(Task.objects.all().count(), 1)
        self.assertEqual(Task.objects.first().code, PROJECT_WAITING_INVOICE)


class TestTaskListView(BaseViewTestCase):
    base_view_name = "list"
    url_name = "todo:{}"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.staff_user = StaffFactory()
        cls.contracting_user = ContractingFactory()
        cls.project = ProjectFactory()
        cls.submission = ApplicationSubmissionFactory()

    def tearDown(self):
        Task.objects.all().delete()

    def test_all_tasks_for_user(self):
        self.assertEqual(Task.objects.all().count(), 0)
        add_task_to_user(
            code=PROJECT_WAITING_INVOICE, user=self.staff_user, related_obj=self.project
        )
        add_task_to_user_group(
            code=PROJECT_WAITING_CONTRACT,
            user_group=Group.objects.filter(name=CONTRACTING_GROUP_NAME),
            related_obj=self.project,
        )
        add_task_to_user_group(
            code=PROJECT_WAITING_PF,
            user_group=Group.objects.filter(name=STAFF_GROUP_NAME),
            related_obj=self.project,
        )

        # staff should have two tests while contracting team member should have a single task
        staff_tasks = get_tasks_for_user(self.staff_user)
        contracting_tasks = get_tasks_for_user(self.contracting_user)

        self.assertEqual(staff_tasks.count(), 2)
        self.assertEqual(contracting_tasks.count(), 1)
        self.assertEqual(contracting_tasks.first().code, PROJECT_WAITING_CONTRACT)

    def test_user_manual_tasks(self):
        self.assertEqual(Task.objects.all().count(), 0)
        activity = ActivityFactory(source=self.project)
        add_task_to_user(
            code=COMMENT_TASK,
            user=self.staff_user,
            related_obj=activity,
        )
        self.client.force_login(user=self.staff_user)
        response = self.get_page()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["my_tasks"]["data"]), 1)
        self.assertEqual(
            len(response.context["my_tasks"]["data"]), Task.objects.all().count()
        )

        comment_task_data = response.context["my_tasks"]["data"][0]
        self.assertEqual(comment_task_data["id"], Task.objects.first().id)
        self.assertEqual(comment_task_data["user"], Task.objects.first().user)

    def test_template_for_submission_actions(self):
        self.assertEqual(Task.objects.all().count(), 0)
        review = ReviewFactory()
        determination = DeterminationFactory()
        add_task_to_user(
            code=SUBMISSION_DRAFT,
            user=self.staff_user,
            related_obj=self.submission,
        )
        add_task_to_user(
            code=DETERMINATION_DRAFT,
            user=self.staff_user,
            related_obj=determination,
        )
        add_task_to_user(
            code=REVIEW_DRAFT,
            user=self.staff_user,
            related_obj=review,
        )
        self.client.force_login(user=self.staff_user)
        response = self.get_page()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["my_tasks"]["data"]), 3)
        self.assertEqual(
            len(response.context["my_tasks"]["data"]), Task.objects.all().count()
        )

        for task_data in response.context["my_tasks"]["data"]:
            self.assertIn(
                task_data["id"], Task.objects.all().values_list("id", flat=True)
            )
            self.assertIn(
                task_data["user"].id, Task.objects.all().values_list("user", flat=True)
            )
            # remove checked task to check other ids
            Task.objects.filter(id=task_data["id"]).delete()
        self.assertEqual(Task.objects.all().count(), 0)

    def test_template_for_project_action_draft_state(self):
        self.assertEqual(Task.objects.all().count(), 0)
        add_task_to_user(
            code=PROJECT_WAITING_PF,
            user=self.staff_user,
            related_obj=self.project,
        )
        add_task_to_user(
            code=PROJECT_WAITING_SOW,
            user=self.staff_user,
            related_obj=self.project,
        )
        add_task_to_user(
            code=PROJECT_SUBMIT_PAF,
            user=self.staff_user,
            related_obj=self.project,
        )
        add_task_to_user(
            code=PAF_REQUIRED_CHANGES,
            user=self.staff_user,
            related_obj=self.project,
        )

        self.client.force_login(user=self.staff_user)
        response = self.get_page()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["my_tasks"]["data"]), 4)
        self.assertEqual(
            len(response.context["my_tasks"]["data"]), Task.objects.all().count()
        )

        for task_data in response.context["my_tasks"]["data"]:
            self.assertIn(
                task_data["id"], Task.objects.all().values_list("id", flat=True)
            )
            self.assertIn(
                task_data["user"].id, Task.objects.all().values_list("user", flat=True)
            )
            # remove checked task to check other ids
            Task.objects.filter(id=task_data["id"]).delete()
        self.assertEqual(Task.objects.all().count(), 0)

    def test_template_for_project_action_internal_approval_state(self):
        self.assertEqual(Task.objects.all().count(), 0)
        add_task_to_user(
            code=PAF_WAITING_ASSIGNEE,
            user=self.staff_user,
            related_obj=self.project,
        )
        add_task_to_user(
            code=PAF_WAITING_APPROVAL,
            user=self.staff_user,
            related_obj=self.project,
        )

        self.client.force_login(user=self.staff_user)
        response = self.get_page()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["my_tasks"]["data"]), 2)
        self.assertEqual(
            len(response.context["my_tasks"]["data"]), Task.objects.all().count()
        )

        for task_data in response.context["my_tasks"]["data"]:
            self.assertIn(
                task_data["id"], Task.objects.all().values_list("id", flat=True)
            )
            self.assertIn(
                task_data["user"].id, Task.objects.all().values_list("user", flat=True)
            )
            # remove checked task to check other ids
            Task.objects.filter(id=task_data["id"]).delete()
        self.assertEqual(Task.objects.all().count(), 0)

    def test_template_for_project_action_contracting_state(self):
        self.assertEqual(Task.objects.all().count(), 0)
        add_task_to_user(
            code=PROJECT_WAITING_CONTRACT,
            user=self.staff_user,
            related_obj=self.project,
        )
        add_task_to_user(
            code=PROJECT_WAITING_CONTRACT_DOCUMENT,
            user=self.staff_user,
            related_obj=self.project,
        )
        add_task_to_user(
            code=PROJECT_WAITING_CONTRACT_REVIEW,
            user=self.staff_user,
            related_obj=self.project,
        )

        self.client.force_login(user=self.staff_user)
        response = self.get_page()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["my_tasks"]["data"]), 3)
        self.assertEqual(
            len(response.context["my_tasks"]["data"]), Task.objects.all().count()
        )

        for task_data in response.context["my_tasks"]["data"]:
            self.assertIn(
                task_data["id"], Task.objects.all().values_list("id", flat=True)
            )
            self.assertIn(
                task_data["user"].id, Task.objects.all().values_list("user", flat=True)
            )
            # remove checked task to check other ids
            Task.objects.filter(id=task_data["id"]).delete()
        self.assertEqual(Task.objects.all().count(), 0)

    def test_template_for_project_action_invoicing_state(self):
        self.assertEqual(Task.objects.all().count(), 0)
        invoice = InvoiceFactory()
        report = ReportFactory()
        add_task_to_user(
            code=PROJECT_WAITING_INVOICE,
            user=self.staff_user,
            related_obj=self.project,
        )
        add_task_to_user(
            code=INVOICE_REQUIRED_CHANGES,
            user=self.staff_user,
            related_obj=invoice,
        )
        add_task_to_user(
            code=INVOICE_WAITING_APPROVAL,
            user=self.staff_user,
            related_obj=invoice,
        )
        add_task_to_user(
            code=INVOICE_WAITING_PAID,
            user=self.staff_user,
            related_obj=invoice,
        )
        add_task_to_user(
            code=REPORT_DUE,
            user=self.staff_user,
            related_obj=report,
        )

        self.client.force_login(user=self.staff_user)
        response = self.get_page()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["my_tasks"]["data"]), 5)
        self.assertEqual(
            len(response.context["my_tasks"]["data"]), Task.objects.all().count()
        )

        for task_data in response.context["my_tasks"]["data"]:
            self.assertIn(
                task_data["id"], Task.objects.all().values_list("id", flat=True)
            )
            self.assertIn(
                task_data["user"].id, Task.objects.all().values_list("user", flat=True)
            )
            # remove checked task to check other ids
            Task.objects.filter(id=task_data["id"]).delete()
        self.assertEqual(Task.objects.all().count(), 0)


class TestTaskManualRemovalView(BaseViewTestCase):
    base_view_name = "delete"
    url_name = "todo:{}"

    def get_kwargs(self, instance):
        return {"pk": instance.id}

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.staff_user = StaffFactory()
        cls.contracting_user = ContractingFactory()
        cls.project = ProjectFactory()

    def tearDown(self):
        Task.objects.all().delete()

    def test_manual_removal_by_user(self):
        self.assertEqual(Task.objects.all().count(), 0)
        add_task_to_user(
            code=PROJECT_WAITING_INVOICE,
            user=self.staff_user,
            related_obj=self.project,
        )
        self.assertEqual(Task.objects.filter(user=self.staff_user).count(), 1)
        self.client.force_login(user=self.staff_user)
        response = self.client.delete(
            self.url(instance=Task.objects.first()),
            data="",
            secure=True,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Task.objects.filter(user=self.staff_user).count(), 0)

    def test_user_cant_remove_others_task(self):
        self.assertEqual(Task.objects.all().count(), 0)
        add_task_to_user(
            code=PROJECT_WAITING_INVOICE,
            user=self.contracting_user,
            related_obj=self.project,
        )
        self.assertEqual(Task.objects.filter(user=self.staff_user).count(), 0)
        self.assertEqual(Task.objects.filter(user=self.contracting_user).count(), 1)
        self.client.force_login(user=self.staff_user)
        response = self.client.delete(
            self.url(instance=Task.objects.first()),
            data="",
            secure=True,
            follow=True,
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Task.objects.filter(user=self.staff_user).count(), 0)
        self.assertEqual(Task.objects.filter(user=self.contracting_user).count(), 1)
