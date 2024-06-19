import time
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Run auto trading loop'

    def autotrading(self, *args, **kwargs):
        print('autotrading')

    def handle(self, *args, **kwargs):
        while True:

            self.autotrading(self, *args, **kwargs)
            print("Running custom trading logic")

            time.sleep(5)
