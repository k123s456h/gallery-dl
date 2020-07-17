# -*- coding: utf-8 -*-
#########################################################
# python
import os
import sys
import traceback
import logging
import threading
import subprocess
import platform
import time
# third-party

# sjva 공용
from framework import db, app, path_app_root, path_data
from framework.logger import get_logger
from framework.util import Util

# 패키지
from .plugin import package_name, logger
from .model import ModelSetting
#########################################################

# path_data = '/app/data'

class Logic(object):
    db_default = { 
        'db_version' : '1',
        'auto_start': 'False',
        'interval': '120',
        'htm_interval': '360',
        'htm_last_update': '1970-01-01',
        'zip': 'True',
        'dfolder': os.path.join(path_data, package_name),
        'downlist': '',
        'blacklist': '',
        'all_download': 'False',
        'gallery-dl_proxy': 'False',
        'gallery-dl_proxy_url': '',
        'gallery-dl_limit-rate': 'False',
        'gallery-dl_limit-rate_value': '',
        'gallery-dl_retries': 'False',
        'gallery-dl_retries_value': '',
        'gallery-dl_sleep': 'False',
        'gallery-dl_sleep_value': '',
        'gallery-dl_auth': 'False',
        'gallery-dl_auth_info': '',
        'gallery-dl_write-metadata': 'False',
        'gallery-dl_option': 'False',
        'gallery-dl_option_value': ''
    }

    @staticmethod
    def db_init():
        try:
            for key, value in Logic.db_default.items():
                if db.session.query(ModelSetting).filter_by(key=key).count() == 0:
                    db.session.add(ModelSetting(key, value))
            db.session.commit()
            
            #Logic.migration()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def plugin_load():
        try:
            logger.debug('%s plugin_load', package_name)
            Logic.db_init()
            if ModelSetting.query.filter_by(key='auto_start').first().value == 'True':
                Logic.scheduler_start()
            # 편의를 위해 json 파일 생성
            from plugin import plugin_info
            Util.save_from_dict_to_json(plugin_info, os.path.join(os.path.dirname(__file__), 'info.json'))
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
    
    @staticmethod
    def plugin_unload():
        try:
            logger.debug('%s plugin_unload', package_name)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    
    @staticmethod
    def scheduler_start():
        try:
            # TODO: import scheduler
            interval = ModelSetting.query.filter_by(key='interval').first().value
            job = Job(package_name, package_name, interval, Logic.scheduler_function, u"%s 설명" % package_name, False)
            scheduler.add_job_instance(job)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    
    @staticmethod
    def scheduler_stop():
        try:
            scheduler.remove_job(package_name)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def scheduler_function():
        #LogicNormal.scheduler_function()
        pass


    @staticmethod
    def reset_db():
        try:
            db.session.query(ModelItem).delete()
            db.session.commit()
            return True
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return False


    @staticmethod
    def one_execute():
        try:
            if scheduler.is_include(package_name):
                if scheduler.is_running(package_name):
                    ret = 'is_running'
                else:
                    scheduler.execute_job(package_name)
                    ret = 'scheduler'
            else:
                def func():
                    time.sleep(2)
                    Logic.scheduler_function()
                threading.Thread(target=func, args=()).start()
                ret = 'thread'
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            ret = 'fail'
        return ret


    @staticmethod
    def process_telegram_data(data):
        try:
            logger.debug(data)
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def migration():
        try:
            pass
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            
#########################################################
####################기본 구조 end#########################
#########################################################

    @staticmethod
    def is_installed():
        try:
            import subprocess
            subprocess.check_output(['gallery-dl', '--version'])
            return True
            # if os.path.exists(target):
            #     return True
            # else:
            #     return False
        except Exception as e: 
            return False
            # logger.error('Exception:%s', e)
            # logger.error(traceback.format_exc())

    @staticmethod
    def install():
        try:
            logger.debug('bbbbbbbbbbbbbbbbbbbbbbb')
            def func():
                logger.debug('aaaaaaaaaaaaaaaaaaa')
                #install_path = '/app/data/custom/gallery-dl/bin/install.sh'
                install_path = '/app/data/plugin/gallery-dl/bin/install.sh'
                os.chmod(install_path, 777)

                import system
                commands = [
                    ['msg', u'잠시만 기다려주세요.'],
                    [install_path],
                    ['msg', u'설치가 완료되었습니다.'],
                    ['msg', u'새로고침하세요.']
                ]
                system.SystemLogicCommand.start('설치', commands)
            t = threading.Thread(target=func, args=())
            t.setDaemon(True)
            t.start()
        except Exception as e:
            logger.error('Exception: %s', e)
            logger.error(traceback.format_exc())

    
    @staticmethod
    def uninstall():
        try:
            def func():
                #uninstall_path = '/app/data/custom/gallery-dl/bin/uninstall.sh'
                uninstall_path = '/app/data/plugin/gallery-dl/bin/uninstall.sh'
                os.chmod(uninstall_path, 777)

                import system
                commands = [
                    ['msg', u'잠시만 기다려주세요.'],
                    [uninstall_path],
                    ['msg', u'제거가 완료되었습니다.'],
                    ['msg', u'새로고침하세요.']
                ]
                system.SystemLogicCommand.start('제거', commands)
            t = threading.Thread(target=func, args=())
            t.setDaemon(True)
            t.start()
        except Exception as e:
            logger.error('Exception: %s', e)
            logger.error(traceback.format_exc())
