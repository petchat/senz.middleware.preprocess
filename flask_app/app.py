# -*- coding: UTF-8 -*-
__author__ = 'woodie, jiaying.lu'

from flask import Flask, request, make_response
import json
import os
from numpy import log

from log2rawsenz import collect_senz_lists
from raw2refine import refine_senz_prob_list
from prob2multi import prob2muti, prob2muti_quick
from config import *

import bugsnag
from bugsnag.flask import handle_exceptions

from logentries import LogentriesHandler
import logging

# Configure Logentries
logger = logging.getLogger('logentries')
if APP_ENV == 'prod':
    logger.setLevel(logging.INFO)
else:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s : %(levelname)s, %(message)s'))
    logger.addHandler(ch)
    logger.setLevel(logging.DEBUG)
logentries_handler = LogentriesHandler(LOGENTRIES_TOKEN)
logger.addHandler(logentries_handler)

# Configure Bugsnag
bugsnag.configure(
    api_key=BUGSNAG_TOKEN,
    project_root=os.path.dirname(os.path.realpath(__file__)),
)

app = Flask(__name__)

# Attach Bugsnag to Flask's exception handler
handle_exceptions(app)


@app.before_first_request
def init_before_first_request():
    import datetime

    init_tag = "[Initiation of Service Process]\n"
    logger.info('[init] enter init_before_first_request')

    log_init_time = "Initiation START at: \t%s\n" % datetime.datetime.now()
    log_app_env = "Environment Variable: \t%s\n" % APP_ENV
    log_bugsnag_token = "Bugsnag Service TOKEN: \t%s\n" % BUGSNAG_TOKEN
    log_logentries_token = "Logentries Service TOKEN: \t%s\n" % LOGENTRIES_TOKEN
    logger.info(init_tag + log_init_time)
    logger.info(init_tag + log_app_env)
    logger.info(init_tag + log_bugsnag_token)
    logger.info(init_tag + log_logentries_token)


@app.route('/log2rawsenz/', methods=['POST'])
def senzCollectorAPI():
    if request.headers.has_key('X-Request-Id') and request.headers['X-Request-Id']:
        x_request_id = request.headers['X-Request-Id']
    else:
        x_request_id = ''

    logger.info('<%s>, [log2rawsenz] request from ip:%s, ua:%s'
                % (x_request_id, request.remote_addr, request.remote_user))
    result = {'code': 1, 'message': ''}

    # params JSON validate
    try:
        incoming_data = json.loads(request.data)
    except ValueError, err_msg:
        logger.exception('<%s>, [log2rawsenz] [ValueError] err_msg: %s, params=%s' % (x_request_id, err_msg, request.data))
        result['message'] = 'Unvalid params: NOT a JSON Object'
        result['code'] = 103
        return make_response(json.dumps(result), 400)

    # params key checking
    for key in ['filter', 'timelines']:
        if key not in incoming_data:
            logger.exception("<%s>, [log2rawsenz] [KeyError] params=%s, should have key: %s" % (x_request_id, incoming_data, key))
            result['message'] = "Params content Error: cant't find key=%s" % (key)
            result['code'] = 103
            return make_response(json.dumps(result), 400)

    logger.info('<%s>, [log2rawsenz] valid request with params=%s' % (x_request_id, incoming_data))

    try:
        result['result'] = collect_senz_lists(incoming_data)
        result['code'] = 0
        result['message'] = 'success'
    except Exception, e:
        logger.exception('<%s>, [log2rawsenz] [Exception] generate result error: %s' % (x_request_id, str(e)))
        result['code'] = 1
        result['message'] = '500 Internal Error'
        return make_response(json.dumps(result), 500)

    logger.info('<%s>, [log2rawsenz] success! result: %s' % (x_request_id, result['result']))
    return json.dumps(result)


@app.route('/raw2refine/', methods=['POST'])
def behaviorCollectorAPI():
    if request.headers.has_key('X-Request-Id'):
        x_request_id = request.headers['X-Request-Id']
    else:
        x_request_id = ''

    logger.info('<%s>, [raw2refine] request from ip:%s, ua:%s' % (x_request_id, request.remote_addr, request.remote_user))
    result = {'code': 1, 'message': ''}

    # params JSON validate
    try:
        incoming_data = json.loads(request.data)
    except ValueError, err_msg:
        logger.error('<%s>, [raw2refine] [ValueError] err_msg: %s, params=%s' % (x_request_id, err_msg, request.data))
        result['message'] = 'Unvalid params: NOT a JSON Object'
        result['code'] = 103
        return make_response(json.dumps(result), 400)

    # params key checking
    try:
        scale_type  = incoming_data['scaleType']
        senz_list   = incoming_data['senzList']
        start_scale_value = incoming_data['startScaleValue']
        end_scale_value = incoming_data['endScaleValue']
    except KeyError, err_msg:
        logger.error('<%s>, [raw2refine] [KeyError] err_msg: %s, params=%s' % (x_request_id, err_msg, incoming_data))
        result['message'] = "Params Contents Error: Can't find keys " \
                            "['scaleType', 'senzList', 'startScaleValue', 'endScaleValue']"
        result['code'] = 103
        return make_response(json.dumps(result), 400)

    try:
        result['result'] = refine_senz_prob_list(scale_type, start_scale_value, end_scale_value, senz_list)
        result['code'] = 0
        result['message'] = 'success'
        logger.info('<%s>, [raw2refine] success!' % (x_request_id))
        return json.dumps(result)
    except Exception, e:
        logger.error('<%s>, [raw2refine] [Exception] generate result error: %s' % (x_request_id, str(e)))
        result['code'] = 1
        result['message'] = '500 Internal Error'
        return make_response(json.dumps(result), 500)


@app.route('/prob2multi/', methods=['POST'])
def senzListConverter():
    result = {'code':1, 'message':''}

    if request.headers.has_key('X-Request-Id'):
        x_request_id = request.headers['X-Request-Id']
    else:
        x_request_id = ''

    logger.info('<%s>, [prob2multi] request from ip:%s, ua:%s' % (x_request_id, request.remote_addr, request.remote_user))

    # params JSON validate
    try:
        params = json.loads(request.data)
    except ValueError, err_msg:
        logger.error('<%s>, [prob2multi] [ValueError] err_msg: %s, params=%s' % (x_request_id, err_msg, request.data))
        result['message'] = 'Unvalid params: NOT a JSON Object'
        result['code'] = 103
        return make_response(json.dumps(result), 400)

    # params key checking
    try:
        prob_senzlist = params['probSenzList']
        strategy = params['strategy']
        mutiSenzList_max_num = params.get('mutiMaxNum', 3)
    except KeyError, err_msg:
        logger.error("<%s>, [prob2mulit] [KeyError] can't find key=%s in params=%s" % (x_request_id, err_msg, params))
        result['message'] = "Params content Error: cant't find key=%s" % (err_msg)
        result['code'] = 103
        return make_response(json.dumps(result), 400)

    logger.info('<%s>, [prob2multi] valid params - prob_senzlist:%s, strategy:%s, mutiSenzList_max_num:%s'
                % (x_request_id, prob_senzlist, strategy, mutiSenzList_max_num))

    # 不同策略不同处理
    if strategy == 'SELECT_MAX_PROB':
        result['code'] = 0
        result['message'] = 'success'
        muti_senzlist = prob2muti(prob_senzlist, log(1e-30))
        muti_senzlist = sorted(muti_senzlist, key=lambda elem: elem['prob'], reverse=True)
        result['result'] = muti_senzlist[:mutiSenzList_max_num]
    if strategy == 'SELECT_MAX_N_PROB':
        result['code'] = 0
        result['message'] = 'success'
        muti_senzlist = prob2muti_quick(prob_senzlist, mutiSenzList_max_num, log(1e-30))
        result['result'] = muti_senzlist
    else:
        logger.error('<%s>, [prob2multi] [Input Error] strategy=%s should in ["SELECT_MAX_PROB", "SELECT_MAX_N_PROB"]'
                      % (x_request_id, strategy))
        result['message'] = 'strategy error'
        result['code'] = 103
        return make_response(json.dumps(result), 400)

    logger.info('<%s>, [prob2multi] success! strategy:%s, code:%s, result:%s'
                %(x_request_id, strategy, result['code'], result['result']))
    return json.dumps(result)


if __name__ == '__main__':
    app.debug = True
    app.run(host="0.0.0.0", port=9010)
