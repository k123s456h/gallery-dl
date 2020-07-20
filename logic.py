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
from framework import db, app, scheduler, path_app_root, path_data
#from framework import db, app, scheduler, path_app_root
from framework.logger import get_logger
from framework.job import Job
from framework.util import Util

# 패키지
from .plugin import package_name, logger
from .model import ModelSetting
from .logic_gallerydl import LogicGalleryDL
#########################################################

#path_data = '/app/data' # for develop

class Logic(object):
    db_default = { 
        'db_version' : '1',
        'auto_start': 'False',
        'interval': '120',
        'htm_interval': '360',
        'htm_last_update': '1970-01-01',
        'pagecount': '1',
        'downlist': '',
        'blacklist': '',
        'all_download': 'False',

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
            
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gallery-dl.conf')) as gdl_conf:
                ModelSetting.set('gallery-dl_option_value', gdl_conf.read())
                gdl_conf.close()

            Logic.db_init()

            # auto start
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
        #LogicNormal.scheduler_function() # get json file and parse it
        pass


    @staticmethod
    def reset_db():
        try:
            db.session.query(ModelgdlItem).delete()
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
            def func():
                #install_path = '/app/data/custom/gallery-dl/bin/install.sh'
                install_path = '/app/data/plugin/gallery-dl/bin/install.sh' # for develop
                os.chmod(install_path, 777)

                import system
                commands = [
                    ['msg', u'잠시만 기다려주세요.'],
                    [install_path],
                    ['msg', u'설치가 완료되었습니다. 새로고침하세요.']
                ]
                system.SystemLogicCommand.start('설치', commands)
            t = threading.Thread(target=func, args=())
            t.setDaemon(True)
            t.start()

            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gallery-dl.conf')) as gdl_conf:
                ModelSetting.set('gallery-dl_option_value', gdl_conf.read())
                gdl_conf.close()

        except Exception as e:
            logger.error('Exception: %s', e)
            logger.error(traceback.format_exc())

    
    @staticmethod
    def uninstall():
        try:
            def func():
                #uninstall_path = '/app/data/custom/gallery-dl/bin/uninstall.sh'
                uninstall_path = '/app/data/plugin/gallery-dl/bin/uninstall.sh' # for develop
                os.chmod(uninstall_path, 777)

                import system
                commands = [
                    ['msg', u'잠시만 기다려주세요.'],
                    [uninstall_path],
                    ['msg', u'제거가 완료되었습니다. 새로고침하세요.']
                ]
                system.SystemLogicCommand.start('제거', commands)
            t = threading.Thread(target=func, args=())
            t.setDaemon(True)
            t.start()
        except Exception as e:
            logger.error('Exception: %s', e)
            logger.error(traceback.format_exc())
    

    # @staticmethod
    # def download(url):
    #     try:

    #     except Exception as e: 
    #             logger.error('Exception:%s', e)
    #             logger.error(traceback.format_exc())
