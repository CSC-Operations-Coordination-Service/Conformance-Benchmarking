from yasube.cases.base import BaseDownloadTestCase


class TestCase821(BaseDownloadTestCase):
    class Meta:
        key = "TestCase821"
        name = "GET Files Download"
        resource_path = "Files"

    def build_url(self, pk: str) -> str:
        return f"{super().build_url(pk)}/$value"
