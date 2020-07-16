# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback

# third-party
from flask import Blueprint, request, render_template, redirect, jsonify 
from flask_login import login_required

# sjva 공용
from framework.logger import get_logger
from framework import app, db, scheduler, path_data, socketio, check_api
from system.model import ModelSetting as SystemModelSetting

# 패키지
package_name = __name__.split('.')[0]
logger = get_logger(package_name)
from .logic import Logic
from .model import ModelSetting
#########################################################

blueprint = Blueprint(package_name, package_name, url_prefix='/%s' %  package_name, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

menu = {
    'main' : [package_name, 'gallery-dl'],
    'sub' : [
        ['setting', '설정'], ['schedule', '작업'],['request', '요청'], ['queue', '큐'],['list', '목록'], ['log', '로그']
    ],
    'category' : 'service'
}

plugin_info = {
    'version' : '0.1.0.0',
    'name' : 'gallery-dl',
    'category_name' : 'service',
    'developer' : 'lapis',
    'description' : 'gallery-dl',
    'home' : 'https://github.com/',
    'more' : '',
}

def plugin_load():
    Logic.plugin_load()

def plugin_unload():
    Logic.plugin_unload()

#########################################################
# WEB Menu   
#########################################################
@blueprint.route('/')
def home():
    return redirect('/%s/setting' % package_name)

@blueprint.route('/<sub>')
@login_required
def first_menu(sub): 
    if sub == 'setting':
        arg = ModelSetting.to_dict()
        arg['package_name']  = package_name
        # arg['tmp_pb_api'] = '%s/%s/api/gallery-dl/%s' % (SystemModelSetting.get('ddns'), package_name, '12548')
        
        if(Logic.is_installed()):
            arg['is_installed'] = True
            try:
                import subprocess
                arg['current_version'] = subprocess.check_output('gallery-dl --version', shell=True)
            except Exception as e:
                arg['current_version'] = 'internal error: '+e
        else:
            arg['is_installed'] = False
            arg['current_version'] = 'not installed'
        
        # if SystemModelSetting.get_bool('auth_use_apikey'):
        #     arg['tmp_pb_api'] += '?apikey=%s' % SystemModelSetting.get('auth_apikey')
        return render_template('{package_name}_{sub}.html'.format(package_name=package_name, sub=sub), arg=arg)
    elif sub == 'log':
        return render_template('log.html', package=package_name)
    return render_template('sample.html', title='%s - %s' % (package_name, sub))

#########################################################
# For UI                                                          
#########################################################
@blueprint.route('/ajax/<sub>', methods=['GET', 'POST'])
@login_required
def ajax(sub):
    try:
        if sub == 'setting_save':
            ret = ModelSetting.setting_save(request)
            return jsonify(ret)
        elif sub == 'status':
            todo = request.form['todo']
            if todo == 'true':
                if Logic.current_process is None:
                    Logic.scheduler_start()
                    ret = 'execute'
                else:
                    ret =  'already_execute'
            else:
                if Logic.current_process is None:
                    ret =  'already_stop'
                else:
                    Logic.scheduler_stop()
                    ret =  'stop'
            return jsonify(ret)
        elif sub == 'install':
            logger.debug('gallery-dl installing...')
            Logic.install()
            return jsonify({})
        elif sub == 'uninstall':
            logger.debug('gallery-dl uninstalling...')
            Logic.uninstall()
            return jsonify({})
    except Exception as e: 
        logger.error('Exception:%s', e)
        logger.error(traceback.format_exc())  

#########################################################
# API - 외부
#########################################################
@blueprint.route('/api/<sub>/<sub2>', methods=['GET', 'POST'])
@check_api
def api(sub, sub2):
    try:
        if sub == 'gallery-dl':
            # from .logic_normal import LogicNormal
            # return LogicNormal.make_gallery-dl(sub2)
            pass
        elif sub == 'klive':
            pass
    except Exception as e:
        logger.debug('Exception:%s', e)
        logger.debug(traceback.format_exc())
