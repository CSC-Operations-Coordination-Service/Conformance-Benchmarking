from yasube.cases.base import BaseListTestCase


class TestCase601(BaseListTestCase):
    class Meta:
        key = "TestCase601"
        name = "GET Subscriptions List"
        resource_path = "Subscriptions"
