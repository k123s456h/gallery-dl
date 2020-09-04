# -*- coding: utf-8 -*-
#########################################################
# 고정영역
#########################################################
# python
import os
import sys
import traceback
import json

# third-party
from flask import Blueprint, request, Response, render_template, redirect, jsonify, url_for, send_from_directory
from flask_login import login_required
from flask_socketio import SocketIO, emit, send

# sjva 공용
from framework.logger import get_logger
from framework import app, db, scheduler, socketio, path_app_root
from framework.util import Util, AlchemyEncoder
from system.logic import SystemLogic
            
# 패키지
package_name = __name__.split('.')[0]
logger = get_logger(package_name)

from .logic import Logic
from .model import ModelSetting
from logic_queue import LogicQueue


blueprint = Blueprint(package_name, package_name, url_prefix='/%s' %  package_name, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

def plugin_load():
    Logic.plugin_load()

def plugin_unload():
    Logic.plugin_unload()

plugin_info = {
    'version' : '0.1.0',
    'name' : 'gallery-dl',
    'category_name' : 'service',
    'icon' : '',
    'developer' : 'lapis',
    'description' : '',
    'home' : 'https://github.com/k123s456h/gallery-dl',
    'more' : '',
}
#########################################################

# 메뉴 구성.
menu = {
    'main' : [package_name, 'gallery-dl'],
    'sub' : [
        ['setting', '설정'], ['scheduler', '자동'], ['request', '요청'], ['queue', '큐'],['list', '목록'], ['log', '로그']
    ],
    'category' : 'service'
}


#########################################################
# WEB Menu
#########################################################
from .logic_hitomi import LogicHitomi

@blueprint.route('/')
def home():
    LogicHitomi.flag = False
    return redirect('/%s/setting' % package_name)
    
@blueprint.route('/<sub>')
@login_required
def first_menu(sub): 
    if sub != 'request':
        LogicHitomi.flag = False

    if sub == 'setting':
        arg = ModelSetting.to_dict()
        arg['package_name']  = package_name
        if(Logic.is_installed()):
            arg['is_installed'] = True
            try:
                import subprocess
                arg['current_version'] = subprocess.check_output(['gallery-dl', '--version']).strip()
            except Exception as e:
                arg['current_version'] = 'internal error: \n' + str(e)
        else:
            arg['is_installed'] = False
            arg['current_version'] = 'not installed'
        
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gallery-dl.conf')) as gdl_conf:
                arg['gallery-dl_option_value'] = gdl_conf.read()
                gdl_conf.close()

        return render_template('{package_name}_{sub}.html'.format(package_name=package_name, sub=sub), arg=arg)
    elif sub == 'scheduler':
        arg = ModelSetting.to_dict()
        arg['package_name']  = package_name
        arg['interval'] = str(int(arg['interval'])/60)
        arg['global_scheduler'] = Logic.schedule_running()
        return render_template('{package_name}_{sub}.html'.format(package_name=package_name, sub=sub), arg=arg)
    elif sub == 'request':
        arg = ModelSetting.to_dict()
        arg['package_name']  = package_name
        arg['is_installed'] = Logic.is_installed()  
        from datetime import datetime
        before = ModelSetting.get('hitomi_last_time')
        arg['data_time'] = before
        arg['outdated'] = (datetime.now() - datetime.strptime(before, '%Y-%m-%d %H:%M:%S')).days >= 1
        arg['is_downloading'] = ModelSetting.get('hitomi_data_status')
        return render_template('{package_name}_{sub}.html'.format(package_name=package_name, sub=sub), arg=arg)
    elif sub == 'queue':
        arg = ModelSetting.to_dict()
        return render_template('{package_name}_{sub}.html'.format(package_name=package_name, sub=sub), arg=arg)
    elif sub == 'list':
        arg = ModelSetting.to_dict()
        return render_template('{package_name}_{sub}.html'.format(package_name=package_name, sub=sub), arg=arg)
    elif sub == 'log':
        return render_template('log.html', package=package_name)
    return render_template('sample.html', title='%s - %s' % (package_name, sub))

#########################################################
# For UI (보통 웹에서 요청하는 정보에 대한 결과를 리턴한다.)
#########################################################
@blueprint.route('/ajax/<sub>', methods=['GET', 'POST'])
@login_required
def ajax(sub):
    logger.debug('[gallery-dl] AJAX %s %s', package_name, sub)
    try:
        if sub == 'setting_save':
            ret = ModelSetting.setting_save(request)
            return jsonify(ret)
        elif sub == 'scheduler':
            enable = ModelSetting.get_bool('enable_searcher')
            go = request.form['scheduler']
            logger.debug('[gallery-dl] scheduler :%s', go)
            if go == 'true':
                Logic.scheduler_start('normal')
                if enable == True:
                    Logic.scheduler_start('data')
                    Logic.scheduler_start('hitomi')
            else:
                Logic.scheduler_stop('normal')
                Logic.scheduler_stop('data')
                Logic.scheduler_stop('hitomi')

            return jsonify(go)
        elif sub == 'one_execute':
            ret = {}
            ret['normal'] = Logic.one_execute('normal')
            ret['hitomi'] = Logic.one_execute('hitomi')
            return jsonify(ret)
        elif sub == 'reset_db':
            ret = Logic.reset_db()
            return jsonify(ret)
        elif sub == 'download_by_request':
            try:
                ret = Logic.download_by_request(request)    # start download from here
                return jsonify(ret)
            except Exception as e: 
                logger.error('[gallery-dl] Exception:%s', e)
                logger.error(traceback.format_exc())
        elif sub == 'completed_remove':
            try:
                from logic_queue import LogicQueue
                ret = LogicQueue.completed_remove()
                return jsonify(ret)
            except Exception as e: 
                logger.error('[gallery-dl] Exception:%s', e)
                logger.error(traceback.format_exc())
        elif sub == 'reset_queue':
            try:
                from logic_queue import LogicQueue
                ret = LogicQueue.reset_queue()
                return jsonify(ret)
            except Exception as e: 
                logger.error('[gallery-dl] Exception:%s', e)
                logger.error(traceback.format_exc())
        elif sub == 'restart_uncompleted':
            try:
                from logic_queue import LogicQueue
                ret = LogicQueue.restart_uncompleted()
                return jsonify(ret)
            except Exception as e:
                logger.error('[gallery-dl] Exception:%s', e)
                logger.error(traceback.format_exc())
        elif sub == 'item_list':
            try:
                ret = Logic.item_list(request)
                return jsonify(ret)
            except Exception as e: 
                logger.error('[gallery-dl] Exception:%s', e)
                logger.error(traceback.format_exc())
        elif sub == 'list_remove':
            try:
                ret = Logic.list_remove(request)
                return jsonify(ret)
            except Exception as e: 
                logger.error('[gallery-dl] Exception:%s', e)
                logger.error(traceback.format_exc())
        elif sub == 'install':
            logger.debug('[gallery-dl] installing...')
            Logic.install()
            return jsonify(True)
        elif sub == 'uninstall':
            logger.debug('[gallery-dl] uninstalling...')
            Logic.uninstall()
            return jsonify(True)
        elif sub == 'default_setting':
            logger.debug('[gallery-dl] restore default gallery-dl.conf...')
            Logic.restore_setting()
            return jsonify(True)
        elif sub == 'bypass':
            logger.debug('[gallery-dl] bypass dpi script installing...')
            Logic.bypass()
            return jsonify(True)
        elif sub == 'undo_bypass':
            logger.debug('[gallery-dl] bypass dpi script uninstalling...')
            Logic.undo_bypass()
            return jsonify(True)
        elif sub == 'data_download':
            logger.debug('[gallery-dl] hitomi data-download')
            import threading
            t = threading.Thread(target=LogicHitomi.download_json, args=())
            t.setDaemon(True)
            t.start()
            return jsonify(True)
    except Exception as e: 
        logger.error('[gallery-dl] Exception:%s', e)
        logger.error(traceback.format_exc())  
        return jsonify('fail')   

    

#########################################################
# socketio
#########################################################
sid_list = []
@socketio.on('connect', namespace='/%s' % package_name)
def connect():
    try:
        logger.debug('[gallery-dl] socket_connect')
        sid_list.append(request.sid)
        send_queue_list()
    except Exception as e: 
        logger.error('[gallery-dl] Exception:%s', e)
        logger.error(traceback.format_exc())


@socketio.on('disconnect', namespace='/%s' % package_name)
def disconnect():
    try:
        sid_list.remove(request.sid)
        logger.debug('[gallery-dl] socket_disconnect')
    except Exception as e: 
        logger.error('[gallery-dl] Exception:%s', e)
        logger.error(traceback.format_exc())

@socketio.on('search', namespace='/%s' % package_name)
def search(arg):
    from .logic_hitomi import LogicHitomi
    LogicHitomi.search(arg)

def socketio_callback(cmd, data, encoding=True):
    if sid_list:
        if encoding:
            data = json.dumps(data, cls=AlchemyEncoder)
            data = json.loads(data)
        socketio.emit(cmd, data, namespace='/%s' % package_name, broadcast=True)


def send_queue_list():
    tmp = LogicQueue.entity_list
    #t = [x.as_dict() for x in tmp]
    #socketio_callback('queue_list', t, encoding=False)
    socketio_callback('queue_list', tmp, encoding=False)

def send_search_result(data):
    socketio_callback('hitomi_search_result', data, encoding=False)

def send_search_one(data):
    socketio_callback('hitomi_result_one', data, encoding=False)
