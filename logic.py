# -*- coding: utf-8 -*-
#########################################################
# python
import os
import sys
import traceback
import logging
import threading
import time
# third-party
from sqlalchemy import desc

# sjva 공용
from framework import db, scheduler, path_data
from framework.job import Job
from framework.util import Util
from framework.logger import get_logger

# 패키지
from .plugin import package_name, logger
from .model import ModelSetting, ModelGalleryDlItem
from .logic_queue import LogicQueue
from .logic_gallerydl import LogicGalleryDL
from .logic_hitomi import LogicHitomi

#########################################################


class Logic(object):
    db_default = { 
        'db_version' : '1',
        'auto_start': 'False',
        'interval': '1440',
        'enable_searcher': 'False',

        'downlist_normal': '',

        'hitomi_last_time': "1970-01-01 00:00:01",
        'hitomi_last_num': "-1",

        'p_title': "",
        "p_artist": "",
        "p_group": "",
        "p_tags": "",
        "p_type": "",
        "p_character": "",
        "p_language": "korean",

        'b_title': "",
        "b_artist": "",
        "b_group": "",
        "b_tags": "",
        "b_type": "",
        "b_character": "",
        "b_language": ""
    }


    @staticmethod
    def db_init():
        try:
            for key, value in Logic.db_default.items():
                if db.session.query(ModelSetting).filter_by(key=key).count() == 0:
                    db.session.add(ModelSetting(key, value))
            db.session.commit()
            Logic.migration()
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def plugin_load():
        try:
            logger.debug('%s plugin_load', package_name)
            # DB 초기화
            Logic.db_init()       
            # 편의를 위해 json 파일 생성
            from plugin import plugin_info
            Util.save_from_dict_to_json(plugin_info, os.path.join(os.path.dirname(__file__), 'info.json'))
            LogicQueue.queue_start()

            # hitomi 데이터 다운로드
            enable = ModelSetting.get_bool('enable_searcher')
            if enable == True:
                from datetime import datetime
                before = ModelSetting.get('hitomi_last_time')
                if (datetime.now() - datetime.strptime(before, '%Y-%m-%d %H:%M:%S')).days >= 1:
                    LogicHitomi.download_json()
            
            # 자동시작 옵션이 있으면 보통 여기서
            if ModelSetting.get_bool('auto_start'):
                Logic.scheduler_start('normal')

                if enable == True:
                    Logic.scheduler_start('hitomi') 
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
    def scheduler_start(sub):
        try:
            logger.debug('%s scheduler_start', package_name+'_'+sub)
            interval = ModelSetting.get('interval')
            job_id = '%s_%s' % (package_name, sub)
            job = Job(package_name, job_id, interval, Logic.scheduler_function, u"gallery-dl_"+sub, False, args=sub)
            scheduler.add_job_instance(job)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def scheduler_stop(sub):
        try:
            job_id = '%s_%s' % (package_name, sub)
            logger.debug('%s scheduler_stop', job_id)
            scheduler.remove_job(job_id)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def scheduler_function(sub):
        try:
            if sub == 'normal':
                LogicGalleryDL.scheduler_function()
            elif sub == 'hitomi':
                LogicHitomi.scheduler_function()
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def one_execute(sub):
        logger.debug("one execute: gallery-dl_%s", sub)
        try:
            job_id = '%s_%s' % (package_name, sub)
            if scheduler.is_include(job_id):
                if scheduler.is_running(job_id):
                    ret = 'is_running'
                else:
                    scheduler.execute_job(job_id)
                    ret = 'scheduler'
            else:
                def func():
                    time.sleep(2)
                    Logic.scheduler_function(sub)
                threading.Thread(target=func, args=()).start()
                ret = 'thread'
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            ret = 'fail'
        return ret


    @staticmethod
    def reset_db():
        try:
            db.session.query(ModelGalleryDlItem).delete()
            db.session.commit()
            return True
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return False


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
                install_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin/install.sh') # for develop
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
        except Exception as e:
            logger.error('Exception: %s', e)
            logger.error(traceback.format_exc())

    
    @staticmethod
    def uninstall():
        try:
            def func():
                #uninstall_path = '/app/data/custom/gallery-dl/bin/uninstall.sh'
                uninstall_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin/uninstall.sh') # for develop
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

    @staticmethod
    def restore_setting():
        try:
            def func():
                import system

                old_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gallery-dl.conf')
                default_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin/gallery-dl-default.conf')
                commands = [
                    ['msg', u'잠시만 기다려주세요.']
                    ['cp', default_config, old_config],
                    ['msg', u'복원이 완료되었습니다. 새로고침하세요.']
                ]

                system.SystemLogicCommand.start('복원', commands)
            t = threading.Thread(target=func, args=())
            t.setDaemon(True)
            t.start()
        except Exception as e:
            logger.error('Exception: %s', e)
            logger.error(traceback.format_exc())
    
    
    @staticmethod
    def bypass():
        try:
            def func():
                install_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin/iptablse.sh')
                os.chmod(install_path, 777)

                import system
                commands = [
                    ['msg', u'잠시만 기다려주세요.'],
                    [install_path],
                    ['msg', u'설치가 완료되었습니다.']
                ]
                system.SystemLogicCommand.start('설치', commands)
            t = threading.Thread(target=func, args=())
            t.setDaemon(True)
            t.start()
        except Exception as e:
            logger.error('Exception: %s', e)
            logger.error(traceback.format_exc())

    
    @staticmethod
    def undo_bypass():
        try:
            def func():
                install_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin/undo_iptables.sh')
                os.chmod(install_path, 777)

                import system
                commands = [
                    ['msg', u'잠시만 기다려주세요.'],
                    [install_path],
                    ['msg', u'제거가 완료되었습니다.']
                ]
                system.SystemLogicCommand.start('제거', commands)
            t = threading.Thread(target=func, args=())
            t.setDaemon(True)
            t.start()
        except Exception as e:
            logger.error('Exception: %s', e)
            logger.error(traceback.format_exc())


    ##################################################################

    @staticmethod
    def download_by_request(req):
        try:
            url = req.form['url']
            url = None if url == '' else url
            from logic_queue import LogicQueue
            if url is not None:
                LogicQueue.add_queue(url)
            else:
                return False
            return True
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return False


    @staticmethod
    def item_list(req):
        try:
            from sqlalchemy import or_

            ret = {}
            page = 1
            page_size = 30
            job_id = ''
            search = ''
            if 'page' in req.form:
                page = int(req.form['page'])
            if 'search_word' in req.form:
                search = req.form['search_word']
            query = db.session.query(ModelGalleryDlItem)
            if search != '':
                #query = query.filter(ModelGalleryDlItem.title.like('%'+search+'%'))
                query = query.filter(or_(ModelGalleryDlItem.title.like('%'+search+'%'),
                                        ModelGalleryDlItem.url.like('%'+search+'%'),
                                        ModelGalleryDlItem.category.like('%'+search+'%') ))


            query = query.order_by(desc(ModelGalleryDlItem.id))
            count = query.count()
            query = query.limit(page_size).offset((page-1)*page_size)
            lists = query.all()
            ret['list'] = [item.as_dict() for item in lists]
            ret['paging'] = Util.get_paging_info(count, page, page_size)
            return ret
        except Exception, e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def list_remove(req):
        try:
            db_id = int(req.form['id'])
            item = db.session.query(ModelGalleryDlItem).filter(ModelGalleryDlItem.id == db_id).first()
            
            if item is not None:
                db.session.delete(item)
                db.session.commit()
            return True
        except Exception, e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return False

    # @staticmethod
    # def list_all_download(req):
    #     try:
    #         db_id = int(req.form['id'])
    #         item = db.session.query(ModelGalleryDlItem).filter(ModelGalleryDlItem.id == db_id).first()
    #         if item is not None:
    #             LogicQueue.add_queue_manga(item.manga_id, False, None)
    #             return True
    #         return False
    #     except Exception, e:
    #         logger.error('Exception:%s', e)
    #         logger.error(traceback.format_exc())
    #         return False

    # @staticmethod
    # def list_add_blacklist(req):
    #     try:
    #         db_id = int(req.form['id'])
    #         item = db.session.query(ModelGalleryDlItem).filter(ModelGalleryDlItem.id == db_id).first()
    #         if item is not None:
    #             from .logic_normal import LogicNormal
    #             tmp = LogicNormal.titlereplace(item.main_title)
    #             entity = db.session.query(ModelSetting).filter_by(key='blacklist').with_for_update().first()
    #             if entity.value.strip() == '':
    #                 entity.value = tmp
    #             else:
    #                 entity.value = entity.value + '|' + tmp
    #             db.session.commit()
    #             return True
    #         return False
    #     except Exception, e:
    #         logger.error('Exception:%s', e)
    #         logger.error(traceback.format_exc())
    #         return False

