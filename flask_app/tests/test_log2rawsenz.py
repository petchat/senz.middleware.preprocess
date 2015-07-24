# -*- coding: utf-8 -*-

"""Unit test for timesequence_align"""

__author__ = 'jiaying.lu'

from unittest import TestCase
import numpy as np

from flask_app.log2rawsenz import _get_sequence_length, _get_sequence_time_length, _get_time_distribution_params, _get_time_distribution
from flask_app.log2rawsenz import _find_nearest_node, _generate_senz_collected
from flask_app.log2rawsenz import generate_sequences_measures, choose_primary_key, collect_senz_lists


class TestMeasuresMethod(TestCase):

    def test_get_sequence_length(self):
        # case 1
        tmp_list = range(10)
        self.assertEqual(10, _get_sequence_length(tmp_list))

        # case 2
        tmp_list = np.arange(10)
        self.assertEqual(10, _get_sequence_length(tmp_list))

    def test_get_sequence_time_length(self):
        # case 1
        tmp_list = [3, 11, 19, 21]
        self.assertEqual(18, _get_sequence_time_length(tmp_list))

        # case 2
        tmp_list = np.array([3, 11, 19, 21])
        self.assertEqual(18, _get_sequence_time_length(tmp_list))

    def test_get_time_distribution_params(self):
        # case 1
        sequence_list = np.array([[1, 3, 6],
                                  [3, 4, 7, 9],
                                  [2, 4, 6, 9]])
        self.assertEqual((2, 2), _get_time_distribution_params(sequence_list))

        # case 2
        sequence_list = np.array([[1],
                                  [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23],
                                  [2, 4, 6, 9]])
        self.assertEqual((3, 7), _get_time_distribution_params(sequence_list))

    def test_get_time_distribution(self):
        # case 1
        sequence = np.array([1, 2])
        self.assertEqual(0, _get_time_distribution(sequence, 1, 2))
        # case 2
        sequence = np.array([1, 2, 3, 4])
        self.assertEqual(0, _get_time_distribution(sequence, 1, 2))

        # case 3
        sequence = np.array([1, 3, 5])
        self.assertEqual(1, _get_time_distribution(sequence, 1, 2))

        # case 4
        sequence = np.array([1, 2, 3, 4, 5, 6])
        self.assertEqual(8, _get_time_distribution(sequence, 1, 2))
        # case 5
        sequence = np.array([1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(8, _get_time_distribution(sequence, 1, 2))


class TestCollectMethod(TestCase):

    def test_find_nearest_node(self):
        # case 1
        primary_node = 3
        node_list = [1, 2, 6, 9]
        self.assertEqual(2, _find_nearest_node(primary_node, node_list))

        # case 2
        primary_node = 3
        node_list = np.array([1, 2, 6, 9])
        self.assertEqual(2, _find_nearest_node(primary_node, node_list))

        # case 3
        primary_node = 12
        node_list = np.array([1, 3, 5, 7, 9, 11])
        self.assertEqual(11, _find_nearest_node(primary_node, node_list))

    def test_generate_senz_collected(self):
        # case 1
        primary_sequence = {'PK': np.array([1, 4, 5, 7, 9])}
        secondary_sequence = {'SK': np.array([3, 5, 8, 9]), 'HK': np.array([2, 5])}
        result = [{'SK': {'timestamp': 1, 'objectId': 'counterfeitObjectId', 'userRawdataId': 'counterfeitRawdataId'}, 'PK': {'timestamp': 1}, 'HK': {'timestamp': 2}},
                  {'SK': {'timestamp': 3}, 'PK': {'timestamp': 4}, 'HK': {'timestamp': 5}},
                  {'SK': {'timestamp': 5}, 'PK': {'timestamp': 5}, 'HK': {'timestamp': 5}},
                  {'SK': {'timestamp': 8}, 'PK': {'timestamp': 7}, 'HK': {'timestamp': 7, 'objectId': 'counterfeitObjectId', 'userRawdataId': 'counterfeitRawdataId'}},
                  {'SK': {'timestamp': 9}, 'PK': {'timestamp': 9}, 'HK': {'timestamp': 9, 'objectId': 'counterfeitObjectId', 'userRawdataId': 'counterfeitRawdataId'}}]
        self.assertEqual(result, _generate_senz_collected(primary_sequence, secondary_sequence, 1))

        # case 2
        primary_sequence = {'PK': np.array([1, 3, 5])}
        secondary_sequence = {'SK': []}
        result = [{'SK': {'timestamp': 1, 'objectId': 'counterfeitObjectId', 'userRawdataId': 'counterfeitRawdataId'}, 'PK': {'timestamp': 1}},
                  {'SK': {'timestamp': 3, 'objectId': 'counterfeitObjectId', 'userRawdataId': 'counterfeitRawdataId'}, 'PK': {'timestamp': 3}},
                  {'SK': {'timestamp': 5, 'objectId': 'counterfeitObjectId', 'userRawdataId': 'counterfeitRawdataId'}, 'PK': {'timestamp': 5}}]
        self.assertEqual(result, _generate_senz_collected(primary_sequence, secondary_sequence, 1))


class TestInterfaceMethod(TestCase):

    def test_generate_sequences_measures(self):
        # case 1
        sequence_list = np.array([[1],
                                  [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]])
        measures = np.array([[1, 0, 0],
                             [11, 20, 48]])
        np.testing.assert_array_equal(measures, generate_sequences_measures(sequence_list))

        # case 2
        sequence_list = np.array([[1],
                                  [3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23],
                                  [1, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]])
        measures = np.array([[1, 0, 0],
                             [11, 20, 48],
                             [13, 18, 42]])
        np.testing.assert_array_equal(measures, generate_sequences_measures(sequence_list))

    def test_choose_primary_key(self):
        timelines = {
            "key0": [{'timestamp': 2}, {'timestamp': 4}, {'timestamp': 6}, {'timestamp': 9}],
            "key1": [{'timestamp': 3}, {'timestamp': 4}, {'timestamp': 7}, {'timestamp': 9}],
            "key2": [],
        }
        self.assertEqual('key0', choose_primary_key(timelines))

    def test_collect_senz_lists(self):
        # case 1
        data = {
            'primary_key': 'HK',
            'filter': 1,
            'timelines': {
                'PK': [{'timestamp': 1}, {'timestamp': 4}, {'timestamp': 5}, {'timestamp': 7}, {'timestamp': 9}],
                'SK': [{'timestamp': 3}, {'timestamp': 5}, {'timestamp': 8}, {'timestamp': 9}],
                'HK': [{'timestamp': 2}, {'timestamp': 5}]
            }
        }
        result = [{'SK': {'timestamp': 1, 'objectId': 'counterfeitObjectId', 'userRawdataId': 'counterfeitRawdataId'}, 'PK': {'timestamp': 1}, 'HK': {'timestamp': 2}},
                  {'SK': {'timestamp': 3}, 'PK': {'timestamp': 4}, 'HK': {'timestamp': 5}},
                  {'SK': {'timestamp': 5}, 'PK': {'timestamp': 5}, 'HK': {'timestamp': 5}},
                  {'SK': {'timestamp': 8}, 'PK': {'timestamp': 7}, 'HK': {'timestamp': 7, 'objectId': 'counterfeitObjectId', 'userRawdataId': 'counterfeitRawdataId'}},
                  {'SK': {'timestamp': 9}, 'PK': {'timestamp': 9}, 'HK': {'timestamp': 9, 'objectId': 'counterfeitObjectId', 'userRawdataId': 'counterfeitRawdataId'}}]
        self.assertEqual(result, collect_senz_lists(data))

        # case 2
        data = {
            'primary_key': 'HK',
            'filter': 1,
            'timelines': {
                'PK': [{'timestamp': 1}, {'timestamp': 3}, {'timestamp': 5}],
                'SK': []
            }
        }
        result = [{'SK': {'timestamp': 1, 'objectId': 'counterfeitObjectId', 'userRawdataId': 'counterfeitRawdataId'}, 'PK': {'timestamp': 1}},
                  {'SK': {'timestamp': 3, 'objectId': 'counterfeitObjectId', 'userRawdataId': 'counterfeitRawdataId'}, 'PK': {'timestamp': 3}},
                  {'SK': {'timestamp': 5, 'objectId': 'counterfeitObjectId', 'userRawdataId': 'counterfeitRawdataId'}, 'PK': {'timestamp': 5}}]
        self.assertEqual(result, collect_senz_lists(data))
