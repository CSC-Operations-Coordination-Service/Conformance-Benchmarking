from yasube.cases.base import BaseDownloadTestCase


class TestCase021(BaseDownloadTestCase):
    class Meta:
        key = "TestCase021"
        name = "GET Products Download"
        resource_path = "Products"

    def build_url(self, pk: str) -> str:
        return f"{super().build_url(pk)}/$value"
