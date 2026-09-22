from html.parser import HTMLParser

from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase


class FormAssociationParser(HTMLParser):
    def __init__(self, target_id):
        super().__init__()
        self.target_id = target_id
        self.current_form_id = None
        self.target_form_id = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "form":
            self.current_form_id = attributes.get("id")
        elif attributes.get("id") == self.target_id:
            self.target_form_id = self.current_form_id

    def handle_endtag(self, tag):
        if tag == "form":
            self.current_form_id = None


class WorkspaceTemplateTests(TestCase):
    def test_neuroglancer_is_not_associated_with_task_form(self):
        user = get_user_model().objects.create_user(
            username="workspace-user",
            password="test-password",
        )
        request = RequestFactory().get("/workspace/test-namespace")
        request.user = user
        html = render_to_string(
            "workspace.html",
            {
                "allowed_to_reassign": False,
                "button_list": [],
                "instructions": {},
                "is_open": True,
                "ng_host": "neuvue",
                "ng_state_plugin": None,
                "ng_url": None,
                "number_of_selected_segments_expected": None,
                "skippable": False,
                "submission_method": "default",
                "submit_task_button": True,
                "tags": "",
                "task_id": "task-id",
                "task_summary": {
                    "namespace_display": "Test namespace",
                    "task_id": "task-id",
                    "seg_id": "1",
                    "pcg_url": "https://example.com",
                    "was_skipped": False,
                    "num_edits": 0,
                    "session_task_count": 0,
                },
                "workspace_config": {},
            },
            request=request,
        )
        parser = FormAssociationParser("neuroglancer-container")
        parser.feed(html)

        self.assertIn('id="mainForm"', html)
        self.assertIsNone(parser.target_form_id)
