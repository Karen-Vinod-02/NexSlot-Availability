from types import SimpleNamespace
from unittest.mock import patch

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase
from django.urls import reverse

from .models import User
from .views import dashboard, upload_document


class CorporateRoleTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def make_request(self, path, role):
        request = self.factory.get(path)
        request.user = User(role=role)
        return request

    def test_employee_is_a_supported_account_role(self):
        self.assertIn(("Employee", "Employee"), User.ROLE_CHOICES)

    def test_employee_dashboard_routes_to_participant_dashboard(self):
        request = self.make_request("/dashboard/", "Employee")

        response = dashboard(request)

        self.assertRedirects(
            response,
            reverse("classroom:student_dashboard"),
            fetch_redirect_response=False,
        )

    @patch("classroom.views.render", return_value=HttpResponse())
    @patch("classroom.views.SystemConfig.get_config")
    def test_employee_can_upload_in_corporate_mode(self, get_config, render):
        get_config.return_value = SimpleNamespace(org_type="Corporate")
        request = self.make_request("/document/upload/", "Employee")

        response = upload_document(request)

        self.assertEqual(response.status_code, 200)
        render.assert_called_once()

    @patch("classroom.views.render", return_value=HttpResponse())
    @patch("classroom.views.SystemConfig.get_config")
    def test_admin_can_upload_in_corporate_mode(self, get_config, render):
        get_config.return_value = SimpleNamespace(org_type="Corporate")
        request = self.make_request("/document/upload/", "Admin")

        response = upload_document(request)

        self.assertEqual(response.status_code, 200)
        render.assert_called_once()

    @patch("classroom.views.SystemConfig.get_config")
    def test_faculty_cannot_upload_in_corporate_mode(self, get_config):
        get_config.return_value = SimpleNamespace(org_type="Corporate")
        request = self.make_request("/document/upload/", "Faculty")

        response = upload_document(request)

        self.assertRedirects(
            response,
            reverse("classroom:dashboard"),
            fetch_redirect_response=False,
        )

    @patch("classroom.views.render", return_value=HttpResponse())
    @patch("classroom.views.SystemConfig.get_config")
    def test_faculty_can_upload_in_college_mode(self, get_config, render):
        get_config.return_value = SimpleNamespace(org_type="College")
        request = self.make_request("/document/upload/", "Faculty")

        response = upload_document(request)

        self.assertEqual(response.status_code, 200)
        render.assert_called_once()

    @patch("classroom.views.SystemConfig.get_config")
    def test_employee_cannot_upload_in_college_mode(self, get_config):
        get_config.return_value = SimpleNamespace(org_type="College")
        request = self.make_request("/document/upload/", "Employee")

        response = upload_document(request)

        self.assertRedirects(
            response,
            reverse("classroom:dashboard"),
            fetch_redirect_response=False,
        )

    @patch("classroom.views.SystemConfig.get_config")
    def test_admin_cannot_upload_in_college_mode(self, get_config):
        get_config.return_value = SimpleNamespace(org_type="College")
        request = self.make_request("/document/upload/", "Admin")

        response = upload_document(request)

        self.assertRedirects(
            response,
            reverse("classroom:dashboard"),
            fetch_redirect_response=False,
        )
