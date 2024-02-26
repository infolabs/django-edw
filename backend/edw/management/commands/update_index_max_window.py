import requests
from haystack.management.commands.update_index import Command as UpdateCommand


ELASTIC_URL = 'http://elasticsearch:9200'
MAX_WINDOW = 100000


class Command(UpdateCommand):
    def handle(self, **options):
        r = requests.put(
            ELASTIC_URL + '/_settings',
            json={'index.max_result_window': MAX_WINDOW},
        )
        print('Updated max result window:', r.text)
        super().handle(**options)
