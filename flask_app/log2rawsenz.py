# -*- coding: utf-8 -*-

"""Align time sequences by length and time distribution"""

__author__ = 'jiaying.lu'
__all__ = ['generate_sequences_measures', 'collect_senz_lists', 'choose_primary_key']

import logging
import numpy as np

logger = logging.getLogger('logentries')
TIME_SEG_NUM = 3


def _get_sequence_length(sequence):
    """Return length of sequence
    """
    return len(sequence)


def _get_sequence_time_length(sequence):
    """Return time length of sequence
    """
    return sequence[-1] - sequence[0]


def _get_time_distribution_params(sequence_list, time_seg_num=TIME_SEG_NUM):
    """Return params of sequences' time distribution

    Parameters
    ----------
    sequence_list: array_like, shape(m, n?)
      List of m time sequence,
      each time sequence may has different elems
    time_seg_num: int, default TIME_SEG_NUM
      时间分段的段数

    Returns
    -------
    time_seq_start: int, timestamp
      时间分布最宽的时间序列的开始时间戳
    time_seg_len: int, in milliseconds
      时间分段的长度
    """
    sequences_time_wide = []
    for sequence in sequence_list:
        # assert not sequence
        sequences_time_wide.append(sequence[-1] - sequence[0])
    time_seg_len = int(round(max(sequences_time_wide) / float(time_seg_num)))

    max_sequence_index = sequences_time_wide.index(max(sequences_time_wide))
    time_seg_start = sequence_list[max_sequence_index][0]

    return time_seg_start, time_seg_len


def _get_time_distribution(sequence, time_seq_start,
                           time_seg_len, time_seg_num=TIME_SEG_NUM):
    """Return time distribution of sequence

    Parameters
    ----------
    sequence: array_like, shape(1, n)
      Time sequence of n timestamp
    time_seq_start: int, timestamp
      时间分布最宽的时间序列的开始时间戳
    time_seg_len: int, in milliseconds
      时间分段的长度
    time_seg_num: int, default TIME_SEG_NUM
      时间分段的段数

    Returns
    -------
    time_dis: float
      measure of time distribution
    """
    sequence_time_slice = lambda sequence, start, end: filter(lambda e: e >= start and e < end, sequence)

    time_dis = 1  # cause time_dis = TT seg_dis(i)
    time_slice_nodes = [(time_seq_start + i * time_seg_len, time_seq_start + (i + 1) * time_seg_len)
                        for i in xrange(time_seg_num)]

    for start, end in time_slice_nodes:
        sequence_seg = sequence_time_slice(sequence, start, end)
        time_dis *= len(sequence_seg)

    return time_dis


def generate_sequences_measures(sequence_list):
    """Generate length, time distribution measures of time sequences

    Parameters
    ----------
    sequence_list: array_like, shape(m, n?)
      List of m time sequence,
      each time sequence may has different elems

    Returns
    -------
    measures: array_like, shape(m, 3)
      Measures of m time sequence,
      each time sequence has 3 measures - length, time length, time dis
    """
    measures = []

    time_seq_start, time_seg_len = _get_time_distribution_params(sequence_list)

    for sequence in sequence_list:
        sequence_length = _get_sequence_length(sequence)
        sequence_time_len = _get_sequence_time_length(sequence)
        sequence_time_dis = _get_time_distribution(sequence, time_seq_start, time_seg_len)
        measures.append([sequence_length, sequence_time_len, sequence_time_dis])

    measures = np.array(measures)
    return measures


def choose_primary_key(timelines):
    """Return primary key of input data

    Primary key has best measures.

    Parameters
    ----------
    timelines: dict, {'key0':, 'key1:, 'key2':, ...}
      raw log data from API request

    Returns
    -------
    primary_key: string, must be one key of data
      primary_key during to best measures
    """
    data_shallow = timelines.copy()  # Use data.copy to avoid change data's attributes

    # filter empty list of data
    sequence_list_keys = filter(lambda e: len(data_shallow[e]) > 0, data_shallow.keys())
    sequence_list_values = filter(lambda e: len(e) > 0, data_shallow.values())

    # generate measures
    sequence_list = []
    for sequence in sequence_list_values:
        sequence = [elem['timestamp'] for elem in sequence]
        sequence_list.append(sequence)
    sequence_list = np.array(sequence_list)
    measures = generate_sequences_measures(sequence_list)

    # find the best measure
    measures_reduced = []
    for measure_list in measures:
        mul_measure = reduce(lambda x, y: x * y, measure_list)
        measures_reduced.append(mul_measure)
    if max(measures_reduced) == 0:  # 乘法的指标容易产生最大为0的结果
        measures_reduced = []
        for measure_list in measures:
            mul_measure = reduce(lambda x, y: x + y, measure_list)
            measures_reduced.append(mul_measure)
    if max(measures_reduced) == 0:  # 如果加法的指标还是0，就返回空结果
        return ''
    best_measure = max(measures_reduced)

    # get primary key
    primary_key = sequence_list_keys[measures_reduced.index(best_measure)]
    # data['primaryKey'] = primary_key  # will change input param

    return primary_key


def _find_nearest_node(primary_node, node_list):
    """Find the most nearest node in node_list with primary_timestamp

    Parameters
    ----------
    primary_node: timestamp
    node_list: array_like, shape(1, n)
      assert len(node_list) > 0
      elems in node_list are pure timestamp

    Returns
    -------
    nearest_node: timestamp
    timestamp in node_list
    """
    sorted_list = list(node_list)
    sorted_list.append(primary_node)
    sorted_list.sort()
    index = sorted_list.index(primary_node)

    if index == 0:
        return sorted_list[index+1]
    if index == len(sorted_list) - 1:
        return sorted_list[index-1]

    return sorted_list[index-1] if abs(sorted_list[index-1]-primary_node) <= abs(sorted_list[index+1]-primary_node) else sorted_list[index+1]


def _find_nearest_timestamp(primary_timestamp, node_list):
    """Find the most nearest node in node_list with primary_timestamp

    Parameters
    ----------
    primary_timestamp: timestamp
    node_list: array_like, shape(1, n)
      elems in node_list are dict, must have a key 'timestamp'

    Returns
    -------
    nearest_node: dict
      node in node_list
    """
    sorted_list = [e['timestamp'] for e in node_list]
    sorted_list.append(primary_timestamp)
    sorted_list.sort()
    index = sorted_list.index(primary_timestamp)

    if index == 0:
        nearest_timestamp = sorted_list[index+1]
    elif index == len(sorted_list) - 1:
        nearest_timestamp = sorted_list[index-1]
    else:
        nearest_timestamp = sorted_list[index-1] if abs(primary_timestamp-sorted_list[index-1]) <= abs(primary_timestamp-sorted_list[index+1]) else sorted_list[index+1]

    for node in node_list:
        if node['timestamp'] == nearest_timestamp:
            return node

    return {}


def _generate_senz_collected(primary_sequence, secondary_sequences, var_filter):
    """Generate pure integer result of senz lists

    Parameters
    ---------
    primary_sequence: dict
      value is array_like, pure integer(timestamp)
    secondary_sequences: dict
      values are array_like, pure integer(timestamp)
    var_filter: float
      secondary sequences' elem variance should less than var_filter

    Returns
    -------
    senz_collected: list,
      [{key0: , key1: , key2:}, {}, {}]
      elem of senz_collected is a senz tuple
    -------
    """
    senz_collected = []
    for primary_key, primary_value in primary_sequence.iteritems():
        for node in primary_value:
            senz_collected_elem = {}
            senz_collected_elem[primary_key] = {'timestamp': node}
            for secondary_key, secondary_value in secondary_sequences.iteritems():
                # handle empty case
                if len(secondary_value) < 1:
                    nearest_node = {
                        "objectId": "counterfeitObjectId",
                        "userRawdataId": "counterfeitRawdataId",
                        "timestamp": node
                    }
                    senz_collected_elem[secondary_key] = nearest_node
                    continue

                nearest_node = {'timestamp': _find_nearest_node(node, secondary_value)}
                if (node - nearest_node['timestamp']) ** 2 > var_filter:
                    nearest_node = {
                        "objectId": "counterfeitObjectId",
                        "userRawdataId": "counterfeitRawdataId",
                        "timestamp": node
                    }
                senz_collected_elem[secondary_key] = nearest_node

            senz_collected.append(senz_collected_elem)

    return senz_collected


def collect_senz_lists(data):
    """Collect senz lists according to primary_key

    Wrapper of _generate_senz_collected, additional add some preprocess.

    Parameters
    ----------
    data: dict, {'filter':, 'primaryKey':, 'timelines':{'key0':, 'key1':, ...}}
      raw log data from API request

    Returns
    -------
    senz_collected: list, [{}, {}, {}]
      elem of senz_collected is a senz tuple
    """
    # Step 1: choose data's primary key
    if not choose_primary_key(data['timelines']):
        primary_key = data['primary_key']
    else:
        primary_key = choose_primary_key(data['timelines'])
    logger.info('[Choose PK] primary_key: %s' % (primary_key))

    # Step 2: generate senz_collected
    # primary_sequence = {primary_key: data['timelines'][primary_key]}
    secondary_sequences = {}
    for key in data['timelines']:
        if key != primary_key:
            secondary_sequences[key] = data['timelines'][key]

    # process sequences
    senz_collected = []
    for p_nodes in data['timelines'][primary_key]:
        senz_collected_elem = {primary_key: p_nodes}
        for secondary_key, secondary_value in secondary_sequences.iteritems():
            # handle empty case
            if len(secondary_value) < 1:
                nearest_node = {
                    "objectId": "counterfeitObjectId",
                    "userRawdataId": "counterfeitRawdataId",
                    "timestamp": p_nodes['timestamp']
                }
                senz_collected_elem[secondary_key] = nearest_node
                continue

            nearest_node = _find_nearest_timestamp(p_nodes['timestamp'], secondary_value)
            if (p_nodes['timestamp'] - nearest_node['timestamp']) ** 2 > data['filter']:
                nearest_node = {
                    "objectId": "counterfeitObjectId",
                    "userRawdataId": "counterfeitRawdataId",
                    "timestamp": p_nodes['timestamp']
                }
            senz_collected_elem[secondary_key] = nearest_node
        senz_collected.append(senz_collected_elem)

    return senz_collected
