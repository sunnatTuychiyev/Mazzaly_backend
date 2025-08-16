from django.test import SimpleTestCase

from recipes.admin import SubmissionActionForm


class SubmissionActionFormTests(SimpleTestCase):
    def test_includes_action_field(self):
        form = SubmissionActionForm()
        self.assertIn('action', form.fields)
