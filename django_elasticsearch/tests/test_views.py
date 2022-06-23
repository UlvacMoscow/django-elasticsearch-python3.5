import mock
import json

from django.test import TestCase

from elasticsearch import TransportError

from django_elasticsearch.managers import es_client

from test_app.models import TestModel


class EsViewTestCase(TestCase):
    def setUp(self):
        # auto index is disabled for tests so we do it manually
        TestModel.es.create_index(ignore=True)
        self.instance = TestModel.objects.create(username="1",
                                                 first_name="woot",
                                                 last_name="foo")
        self.instance.es.do_index()
        TestModel.es.do_update()

    def tearDown(self):
        super(EsViewTestCase, self).tearDown()
        es_client.indices.delete(index=TestModel.es.get_index())

    def _test_detail_view(self):
        response = self.client.get('/tests/{id}/'.format(id=self.instance.pk))
        content = json.loads(response.content)
        self.assertEqual(content['fields']['first_name'], "woot")
        self.assertEqual(content['fields']['last_name'], "foo")

    def test_detail_view(self):
        self._test_detail_view()

    def test_404(self):
        resp = self.client.get('/tests/{0}/'.format(self.instance.pk + 10))
        resp.status_code = 404

    def test_fallback_detail_view(self):
        with mock.patch('django_elasticsearch.query.EsQueryset.get') as mock_get:
            mock_get.side_effect = TransportError()
            self._test_detail_view()

    def _test_list_view(self):
        response = self.client.get('/tests/')
        content = json.loads(response.content)
        self.assertEqual(content[0]['fields']['first_name'], "woot")
        self.assertEqual(content[0]['fields']['last_name'], "foo")

    def test_list_view(self):
        self._test_list_view()

    def test_fallback_list_view(self):
        with mock.patch('django_elasticsearch.query.EsQueryset.do_search') as mock_search:
            mock_search.side_effect = TransportError()
            response = self.client.get('/tests/')
            content = json.loads(response.content)
            self.assertEqual(len(content), 1)
            self.assertEqual(content[0]['fields']['first_name'], "woot")
            self.assertEqual(content[0]['fields']['last_name'], "foo")
