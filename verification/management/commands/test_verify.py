from django.core.management.base import BaseCommand
from django.test import Client

class Command(BaseCommand):
    help = "Test the /verification/verify/ endpoint"

    def handle(self, *args, **options):
        client = Client()
        response = client.post('/verification/verify/', data={}, follow=True)

        self.stdout.write(f"Status Code: {response.status_code}")
        self.stdout.write(f"Response: {response.content.decode()}")
