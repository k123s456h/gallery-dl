# -*- coding: utf-8 -*-
#########################################################
# python
import os
import sys
import traceback
import logging
import threading
import Queue
import json
# third-party

# sjva 공용
from framework import db, scheduler, path_data, celery, app
from framework.job import Job
from framework.util import Util

# 패키지
import system
from .plugin import package_name, logger
from .model import ModelGalleryDlItem
from .logic_gallerydl import LogicGalleryDL


#########################################################

class LogicQueue(object):
    download_queue = None
    download_thread = None
    entity_list = []

    @staticmethod
    def queue_start():
        try:
            if LogicQueue.download_queue is None:
                LogicQueue.download_queue = Queue.Queue()
            
            if LogicQueue.download_thread is None:
                LogicQueue.download_thread = threading.Thread(target=LogicQueue.download_thread_function, args=())
                LogicQueue.download_thread.daemon = True  
                LogicQueue.download_thread.start()
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def download_thread_function():
        while True:
            try:
                entity = LogicQueue.download_queue.get()
                logger.debug('Queue receive item: %s', entity['url'])

                if entity['status'] == '완료':
                    entity['status'] = '중복'
                    entity['index'] = int(entity['total_image_count'])
                    LogicGalleryDL.entity_update('queue_one', entity)
                else:
                    if app.config['config']['use_celery']:
                        result = LogicGalleryDL.make_download.apply_async((entity,))
                        result.get(on_message=LogicGalleryDL.update, propagate=True)
                    else:
                        LogicGalleryDL.make_download(entity)
                    
                    #LogicGalleryDL.download(entity)
                #LogicGalleryDL.download(entity)
                #LogicQueue.download_queue.task_done()    
            except Exception as e: 
                logger.error('Exception:%s', e)
                logger.error(traceback.format_exc())

    @staticmethod
    def add_queue(url):
        try:
            entity = ModelGalleryDlItem.add(url)
            if entity is not None:
                for idx, e in enumerate(LogicQueue.entity_list):
                    if e['url'] == entity['url']:
                        del LogicQueue.entity_list[idx]
                        #return
                LogicQueue.entity_list.append(entity)
                LogicQueue.download_queue.put(entity)
            return entity
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
    
    @staticmethod
    def completed_remove():
        try:
            new_list = []
            for e in LogicQueue.entity_list:
                if e['status'] not in ['완료', '중복']:
                    new_list.append(e)
            LogicQueue.entity_list = new_list
            import plugin
            plugin.send_queue_list()
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def reset_queue():
        try:
            with LogicQueue.download_queue.mutex:
                LogicQueue.download_queue.queue.clear()
            LogicQueue.entity_list = []
            import plugin
            plugin.send_queue_list()
            #LogicMD.stop()
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def restart_uncompleted():
        try:
            new_list = []
            failed_list = []
            for e in LogicQueue.entity_list:
                if e['status'] not in ['실패: url', '실패: 차단된 사이트', '실패']:
                    new_list.append(e)
                else:
                    failed_list.append(e)
            for e in failed_list:
                LogicQueue.download_queue.put(e)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())