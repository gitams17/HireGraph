import io
import zipfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from organizations.models import Organization, OrganizationMembership, OrganizationRole
from .models import Candidate, Resume

User = get_user_model()


def make_valid_pdf_file(filename="test_resume.pdf"):
    # Starts with %PDF-
    content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    return SimpleUploadedFile(filename, content, content_type="application/pdf")


def make_valid_docx_file(filename="test_resume.docx"):
    # Creates an in-memory ZIP package with [Content_Types].xml
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", b'<?xml version="1.0" encoding="UTF-8"?><Types></Types>')
        zf.writestr("word/document.xml", b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"></w:document>')
    buf.seek(0)
    return SimpleUploadedFile(
        filename,
        buf.read(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


class CandidateTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="recruiter@example.com",
            password="StrongPassword123!",
            first_name="Jane",
            last_name="Recruiter",
        )
        self.org = Organization.objects.create(name="Acme Corp", slug="acme-corp")
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org,
            role=OrganizationRole.RECRUITER,
        )

        # Other user & org for isolation tests
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="StrongPassword123!",
            first_name="Other",
            last_name="Person",
        )
        self.other_org = Organization.objects.create(name="Other Corp", slug="other-corp")
        OrganizationMembership.objects.create(
            user=self.other_user,
            organization=self.other_org,
            role=OrganizationRole.RECRUITER,
        )

        self.client.force_authenticate(user=self.user)

    def test_create_candidate(self):
        payload = {
            "organization": str(self.org.id),
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice.smith@example.com",
            "phone": "+1-555-0199",
            "current_company": "Tech Innovators",
            "current_title": "Full Stack Engineer",
            "total_experience_years": 4,
            "skills": ["Python", "Django", "TypeScript", "React"],
        }
        res = self.client.post("/api/v1/candidates/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["full_name"], "Alice Smith")
        self.assertTrue(Candidate.objects.filter(email="alice.smith@example.com").exists())

    def test_candidate_org_isolation(self):
        candidate = Candidate.objects.create(
            organization=self.org,
            first_name="Bob",
            last_name="Jones",
            email="bob@example.com",
        )

        # Authenticate as other_user from other_org
        self.client.force_authenticate(user=self.other_user)
        res = self.client.get(f"/api/v1/candidates/{candidate.id}/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # List should not include candidate
        res_list = self.client.get("/api/v1/candidates/")
        self.assertEqual(len(res_list.data["results"]), 0)

    def test_duplicate_candidate_email_rejected(self):
        Candidate.objects.create(
            organization=self.org,
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
        )
        payload = {
            "organization": str(self.org.id),
            "first_name": "Alice",
            "last_name": "Different",
            "email": "alice@example.com",
        }
        res = self.client.post("/api/v1/candidates/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("email" in res.data or "non_field_errors" in res.data)

    def test_upload_valid_pdf_resume(self):
        candidate = Candidate.objects.create(
            organization=self.org,
            first_name="David",
            last_name="Miller",
            email="david@example.com",
        )
        pdf_file = make_valid_pdf_file("david_resume.pdf")

        res = self.client.post(
            f"/api/v1/candidates/{candidate.id}/resumes/",
            {"file": pdf_file, "is_primary": "true"},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["file_name"], "david_resume.pdf")
        self.assertTrue(Resume.objects.filter(candidate=candidate).exists())

    def test_upload_valid_docx_resume(self):
        candidate = Candidate.objects.create(
            organization=self.org,
            first_name="Eve",
            last_name="Taylor",
            email="eve@example.com",
        )
        docx_file = make_valid_docx_file("eve_resume.docx")

        res = self.client.post(
            f"/api/v1/candidates/{candidate.id}/resumes/",
            {"file": docx_file, "is_primary": "true"},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["file_name"], "eve_resume.docx")
        self.assertTrue(Resume.objects.filter(candidate=candidate).exists())

    def test_upload_fake_pdf_rejected(self):
        candidate = Candidate.objects.create(
            organization=self.org,
            first_name="Frank",
            last_name="Fake",
            email="frank@example.com",
        )
        # Text file pretending to be a PDF
        fake_file = SimpleUploadedFile("malicious.pdf", b"echo 'harmful script'", content_type="application/pdf")

        res = self.client.post(
            f"/api/v1/candidates/{candidate.id}/resumes/",
            {"file": fake_file},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", res.data)

    def test_upload_fake_docx_rejected(self):
        candidate = Candidate.objects.create(
            organization=self.org,
            first_name="Grace",
            last_name="Hopper",
            email="grace@example.com",
        )
        fake_file = SimpleUploadedFile("fake.docx", b"not a zip file", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        res = self.client.post(
            f"/api/v1/candidates/{candidate.id}/resumes/",
            {"file": fake_file},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", res.data)

    def test_download_resume_authenticated(self):
        candidate = Candidate.objects.create(
            organization=self.org,
            first_name="Helen",
            last_name="Troy",
            email="helen@example.com",
        )
        pdf_file = make_valid_pdf_file("helen_cv.pdf")
        upload_res = self.client.post(
            f"/api/v1/candidates/{candidate.id}/resumes/",
            {"file": pdf_file},
            format="multipart",
        )
        resume_id = upload_res.data["id"]

        download_res = self.client.get(f"/api/v1/candidates/{candidate.id}/resumes/{resume_id}/download/")
        self.assertEqual(download_res.status_code, status.HTTP_200_OK)
        self.assertEqual(download_res.headers["Content-Type"], "application/pdf")

        # Other org user cannot download
        self.client.force_authenticate(user=self.other_user)
        denied_res = self.client.get(f"/api/v1/candidates/{candidate.id}/resumes/{resume_id}/download/")
        self.assertEqual(denied_res.status_code, status.HTTP_404_NOT_FOUND)
