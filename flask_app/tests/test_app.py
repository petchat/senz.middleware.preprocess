# -*- coding: UTF-8 -*-

"""Unit test for app.py"""

__author__ = 'jiaying.lu'

from unittest import TestCase
from flask_app.app import app
import json


class TestSenzCollectorAPI(TestCase):
    url = '/log2rawsenz/'

    def setUp(self):
        super(TestSenzCollectorAPI, self).setUp()
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        super(TestSenzCollectorAPI, self).tearDown()
        app.config['TESTING'] = False

    def test_empty_params(self):
        rv = self.app.post(self.url, data='')
        self.assertEqual(400, rv.status_code)
        result = json.loads(rv.data)
        self.assertEqual(103, result['code'])

    def test_unvalid_params(self):
        rv = self.app.post(self.url, data='OhMyParams')
        self.assertEqual(400, rv.status_code)
        result = json.loads(rv.data)
        self.assertEqual(103, result['code'])

        # case 2
        data = {
            'primary_key': 'HK',
            'filter': 1,
            'timelines': {
                'PK': [{'timestamp': 1}, {'timestamp': 3}, {'timestamp': 5}],
                'SK': [1, {'test': 2}, 'error_key']
            }
        }
        rv = self.app.post(self.url, data=json.dumps(data))
        self.assertEqual(400, rv.status_code)
        result = json.loads(rv.data)
        self.assertEqual(103, result['code'])

    def test_valid_params(self):
        # case 1
        data = {
            "primary_key": "HK",
            "filter": 1,
            "timelines": {
                "PK": [{"timestamp": 1}, {"timestamp": 3}, {"timestamp": 5}],
                "SK": []
            }
        }
        rv = self.app.post(self.url, data=json.dumps(data))
        self.assertEqual(200, rv.status_code)
        result = json.loads(rv.data)
        self.assertEqual(0, result['code'])
        senz_collected = [
            {'SK': {'timestamp': 1, 'objectId': 'counterfeitObjectId', 'userRawdataId': 'counterfeitRawdataId'},
             'PK': {'timestamp': 1}},
            {'SK': {'timestamp': 3, 'objectId': 'counterfeitObjectId', 'userRawdataId': 'counterfeitRawdataId'},
             'PK': {'timestamp': 3}},
            {'SK': {'timestamp': 5, 'objectId': 'counterfeitObjectId', 'userRawdataId': 'counterfeitRawdataId'},
             'PK': {'timestamp': 5}}]
        self.assertEqual(senz_collected, result['result'])

        # case 2
        data = {
            "primary_key": "HK",
            "filter": 1,
            "timelines": {
                "PK": [{"timestamp": 1, 'objectId': 'o1', 'userRawdataId': 'u1'},
                       {"timestamp": 3, 'objectId': 'o3', 'userRawdataId': 'u3'},
                       {"timestamp": 5, 'objectId': 'o5', 'userRawdataId': 'u5'}],
                "SK": [{"timestamp": 1, 'objectId': 'So1', 'userRawdataId': 'uS1'},
                       {"timestamp": 3, 'objectId': 'So3', 'userRawdataId': 'uS3'},
                       {"timestamp": 5, 'objectId': 'So5', 'userRawdataId': 'uS5'}],
            }
        }
        rv = self.app.post(self.url, data=json.dumps(data))
        self.assertEqual(200, rv.status_code)
        result = json.loads(rv.data)
        self.assertEqual(0, result['code'])
