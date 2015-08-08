# -*- coding: UTF-8 -*-

__author__ = ['MeoWoodie', 'jiaying.lu']

__all__ = ['BehaviorCollector', 'refine_senz_prob_list']


# configs
MAX_SCALE_VALUE = {
    'perMinScale': 1439,
    'tenMinScale': 143,
    'halfHourScale': 47,
    'perHourScale': 23
}
K_WEIGHT_DEFAULT = 0.5  # default value for _collect_probs() param k_weight

# def CountStrategy(sensor_type_list):
#     # Calculate the new senz's motion type
#     # The new senz's motion type is much more than other type in senzes' motion type in list.
#     _sensor_type = ''
#     sensor_type_count = {}
#     # - calculate the count of every type in list.
#     for sensor_type in sensor_type_list:
#         if sensor_type in sensor_type_count.keys():
#             sensor_type_count[sensor_type] += 1
#         else:
#             sensor_type_count[sensor_type] = 0
#     # - select the largest count.
#     max_count = 0
#     for type in sensor_type_count.keys():
#         if sensor_type_count[type] >= max_count:
#             max_count = sensor_type_count[type]
#             _sensor_type = type
#
#     print 'The largest type is', type, '. the count of it is', max_count
#     return _sensor_type

def FirstStrategy(sensor_type_list):
    return sensor_type_list[0]

def BehaviorCollector(input_data):
    '''
    Behavior Collector

    It's used for getting a general senz tuple from a senz list.
    Senz from the list has the same scale value.
    We assumed that they have a general attribute cause of being generated at same time.

    :return: A general senz tuple, with motion type, sound type and poi type.
    '''
    # Extract the information from senz list
    timestamp_list   = []
    motion_prob_list = []
    poi_prob1_list   = []
    poi_prob2_list   = []
    sound_prob_list  = []
    for senz_tuple in input_data:
        timestamp_list.append(senz_tuple['timestamp'])
        motion_prob_list.append(senz_tuple['motionProb'])
        poi_prob1_list.append(senz_tuple['poiProbLv1'])
        poi_prob2_list.append(senz_tuple['poiProbLv2'])
        sound_prob_list.append(senz_tuple['soundProb'])

    # Calculate the new senz's timestamp
    # It is the average of senzes' timestamp in list.
    _timestamp = 0
    for timestamp in timestamp_list:
        _timestamp += timestamp
    _timestamp /= len(timestamp_list)

    # Calculate every sensor's type.
    _motion_prob = FirstStrategy(motion_prob_list)
    _poi_prob1   = FirstStrategy(poi_prob1_list)
    _poi_prob2   = FirstStrategy(poi_prob2_list)
    _sound_prob  = FirstStrategy(sound_prob_list)

    result = {
        'motionProb': _motion_prob,
        'poiProbLv1': _poi_prob1,
        'poiProbLv2': _poi_prob2,
        'soundProb': _sound_prob,
        'timestamp': _timestamp
    }
    print 'The new senz tuple is'
    print result

    return result


def _get_arithmetic_average(prob_list):
    """Calculate arithmetic average of prob_list

    Parameters
    ----------
    prob_list: array_like, shape(1, n)
      elems are dict, with string keys and float values

    Returns
    -------
    prob_result: dict
      with string keys and float values
    """
    prob_result = {}
    prob_length = len(prob_list)

    for elem in prob_list:
        for elem_key in elem:
            if prob_result.has_key(elem_key):
                prob_result[elem_key] += elem[elem_key]
            else:
                prob_result[elem_key] = elem[elem_key]

    for prob_key in prob_result:
        prob_result[prob_key] /= prob_length

    return prob_result


def _collect_probs(cur_prob_list, other_prob_list, k_weight=K_WEIGHT_DEFAULT):
    """Collect probs in cur_prob_list, during

    Parameters
    ----------
    cur_prob_list: array_like, shape(1, n)
      elems are dict, with string keys and float values
    other_prob_list: array_like, shape(1, m)
      elems are dict, with string keys and float values
    k_weight: float, limit [0, 1]
      weight for cur_prob_list, represent cur_prob_list's weight in total
      if k_weight out of [0, 1], will use a default value

    Returns
    -------
    prob_result: dict
      with string keys and float values
    """
    if k_weight < 0 or k_weight > 1:
        k_weight = K_WEIGHT_DEFAULT

    if isinstance(cur_prob_list, dict):
        cur_prob_list = [cur_prob_list]
    if isinstance(other_prob_list, dict):
        other_prob_list = [other_prob_list]

    cur_prob_result = _get_arithmetic_average(cur_prob_list)
    other_prob_result = _get_arithmetic_average(other_prob_list)

    # process with k_weight
    for key in cur_prob_result:
        cur_prob_result[key] *= (2 * k_weight)
    for key in other_prob_result:
        other_prob_result[key] *= (2 * (1-k_weight))

    prob_list = [cur_prob_result, other_prob_result]

    return _get_arithmetic_average(prob_list)


def _check_blank_condition(start, end, my_list, max_blank_num=2):
    """Check my_list's blank condition.

    if continuous blank num gt max_blank_num, return False;
    Otherwise return True.

    Parameters
    ----------
    start: int
    end: int
    my_list: list, shape(1, n)
      elems are int

    Returns
    -------
    blank_condition: bool
    """
    if len(my_list) < 1:
        return False

    if my_list[0] - start >= max_blank_num or end - my_list[-1] >= max_blank_num:
        return False

    for index in xrange(len(my_list) - 1):
        if abs(my_list[index] - my_list[index+1]) > max_blank_num:
            return False

    return True


def refine_senz_prob_list(scale_type, start_scale_value, end_scale_value, senz_prob_list):
    """ Generate a refined senz prob list according to the scale type and scale values

    如果 senz_prob_list 按照scale_type切割出来的小格子中连续出现了 max_blank_senz_prob (default 2)个,
    则此次传入的senz_prob_list视为无效的，返回code=1的结果。
    如果 没有上述情况，则对空缺的小格子进行补空操作，策略是取相邻格子的算术平均

    Parameters
    ----------
    scale_type: string
      must in ['tenMinScale', 'halfHourScale', 'perHourScale']
    start_scale_value: int
      senz_prob_list[index][scale_type] start value
    end_scale_value: int
      senz_prob_list[index][scale_type] end value
    senz_prob_list: list, shape(1, n)
      elems are dict, contains prob_lists, timestamp, scale_values, senzId

    Returns
    -------
    refined_senz_prob_list: list, shape(1, m)
      m <= n
    """
    start_scale_value = int(start_scale_value)
    end_scale_value = int(end_scale_value)

    max_blank_senz_prob = 2
    refined_senz_prob_list = []

    if start_scale_value == end_scale_value:
        return []

    # Step 0: check start, end
    checked_senz_prob_list = []
    for elem in senz_prob_list:
        if start_scale_value < end_scale_value and start_scale_value <= elem[scale_type] <= end_scale_value:
            checked_senz_prob_list.append(elem)
        if start_scale_value > end_scale_value:
            if elem[scale_type] <= end_scale_value:
                elem[scale_type] += (MAX_SCALE_VALUE[scale_type] + 1)
            checked_senz_prob_list.append(elem)

    if start_scale_value > end_scale_value:
        shadow_end_scale_values = end_scale_value
        end_scale_value += MAX_SCALE_VALUE[scale_type]

    senz_prob_list = checked_senz_prob_list

    # Step 1: process scale
    scaled_senz_prob_list = []
    scaled_senz_prob_dict = {}
    for elem in senz_prob_list:
        elem_scale_value = elem[scale_type]
        if elem_scale_value in scaled_senz_prob_dict:
            scaled_senz_prob_dict[elem_scale_value].append(elem)
        else:
            scaled_senz_prob_dict[elem_scale_value] = [elem]

    for sorted_key in sorted(scaled_senz_prob_dict):
        scaled_senz_prob_list.append(scaled_senz_prob_dict[sorted_key])

    # Step 2: check blank condition
    if not _check_blank_condition(start_scale_value, end_scale_value, sorted(scaled_senz_prob_dict), max_blank_senz_prob):
        return []

    # Step 3: calculate per scale combined prob
    combined_prob_list = []

    total_prob_dict = {}
    total_prob_keys = [key for key in scaled_senz_prob_list[0][0].iterkeys() if key not in ['timestamp', 'senzId', 'tenMinScale', 'halfHourScale', 'perHourScale', 'perMinScale']]
    for key in total_prob_keys:
        total_prob_dict[key] = []
    for per_scaled_list in scaled_senz_prob_list:
        for per_dict in per_scaled_list:
            for key in total_prob_keys:
                total_prob_dict[key].append(per_dict[key])

    for per_scaled_list in scaled_senz_prob_list:
        cur_prob_dict = {}
        for key in total_prob_keys:
            cur_prob_dict[key] = []
        cur_average_timestamp = 0
        cur_scale_value = per_scaled_list[0][scale_type]
        cur_senz_ids = []
        for per_dict in per_scaled_list:
            cur_average_timestamp += per_dict['timestamp']
            cur_senz_ids.append(per_dict['senzId'])
            for key in total_prob_keys:
                cur_prob_dict[key].append(per_dict[key])
        cur_average_timestamp = int(cur_average_timestamp / len(per_scaled_list))
        combined_prob_list_elem = {
            'timestamp': cur_average_timestamp,
            scale_type: cur_scale_value,
            'senzId': cur_senz_ids
        }
        for key in total_prob_keys:
            # print('cur_prob_dict[%s]:%s' % (key, cur_prob_dict[key]))
            # print('total_prob_dict[%s]:%s' % (key, total_prob_dict[key]))
            combined_prob_list_elem[key] = _collect_probs(cur_prob_dict[key], total_prob_dict[key], k_weight=0.75)

        combined_prob_list.append(combined_prob_list_elem)

    # Step 4: fill blank scales
    for index in xrange(len(combined_prob_list)):
        refined_senz_prob_list.append(combined_prob_list[index])
        if index == len(combined_prob_list) - 1:
            break
        if combined_prob_list[index+1][scale_type] - combined_prob_list[index][scale_type] == max_blank_senz_prob:
            refined_senz_prob_list_elem = {
                'timestamp': (combined_prob_list[index]['timestamp'] + combined_prob_list[index+1]['timestamp']) / 2,
                #'motionProb': _collect_probs(combined_prob_list[index]['motionProb'], combined_prob_list[index+1]['motionProb'], k_weight=0.5),
                scale_type: combined_prob_list[index][scale_type] + 1,
                'senzId': []
            }
            for key in total_prob_keys:
                refined_senz_prob_list_elem[key] = _collect_probs(combined_prob_list[index][key], combined_prob_list[index+1][key], k_weight=0.5)

            refined_senz_prob_list.append(refined_senz_prob_list_elem)

    if end_scale_value > MAX_SCALE_VALUE[scale_type]:
        end_scale_value = shadow_end_scale_values
        tmp_refiend_senz_prob_list = list(refined_senz_prob_list)
        refined_senz_prob_list = []
        for refined_senz_prob in tmp_refiend_senz_prob_list:
            if refined_senz_prob[scale_type] > MAX_SCALE_VALUE[scale_type]:
                refined_senz_prob[scale_type] -= (MAX_SCALE_VALUE[scale_type] + 1)
            refined_senz_prob_list.append(refined_senz_prob)

    # 补全开始结尾处的空白
    if combined_prob_list[0][scale_type] - start_scale_value == 1:
        refined_senz_prob_list_elem = {
            'timestamp': combined_prob_list[0]['timestamp'],
            scale_type: start_scale_value,
            'senzId': []
        }
        for key in total_prob_keys:
            refined_senz_prob_list_elem[key] = combined_prob_list[0][key]
        refined_senz_prob_list.insert(0, refined_senz_prob_list_elem)

    if end_scale_value - combined_prob_list[-1][scale_type] == 1:
        refined_senz_prob_list_elem = {
            'timestamp': combined_prob_list[-1]['timestamp'],
            scale_type: end_scale_value,
            'senzId': []
        }
        for key in total_prob_keys:
            refined_senz_prob_list_elem[key] = combined_prob_list[-1][key]
        refined_senz_prob_list.append(refined_senz_prob_list_elem)

    return refined_senz_prob_list



if __name__ == '__main__':
    # case 2
    scale_type = "perHourScale"
    senz_prob_list = [
        {
            "motionProb": {"A": 0.7, "B": 0.3},
            "locationProb": {"A": 0.7, "B": 0.3},
            "timestamp": 21921921213,
            "perHourScale": 23,
            "senzId": 11
        },
        {
            "motionProb": {"A": 0.3, "C": 0.7},
            "locationProb": {"A": 0.3, "C": 0.7},
            "timestamp": 11223333,
            "perHourScale": 23,
            "senzId": 12
        },
        {
            "motionProb": {"B": 0.7, "C": 0.3},
            "locationProb": {"B": 0.7, "C": 0.3},
            "timestamp": 333222,
            "perHourScale": 0,
            "senzId": 21
        },
        {
            "motionProb": {"A": 0.7, "C": 0.3},
            "locationProb": {"A": 0.7, "C": 0.3},
            "timestamp": 992222,
            "perHourScale": 2,
            "senzId": 41
        },
    ]
    print(refine_senz_prob_list(scale_type, 23, 2, senz_prob_list))
