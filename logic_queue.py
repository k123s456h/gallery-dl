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

SIZE = 4

class LogicQueue(object):
    static_index = 0
    download_queue = []
    download_thread = []
    entity_list = []

    @staticmethod
    def queue_start():
        try:
            for i in range(0, SIZE):
                LogicQueue.download_queue.append( Queue.Queue() )
                LogicQueue.download_thread.append( threading.Thread(target=LogicQueue.download_thread_function, args=(i,)) )

            for i in range(0, SIZE):
                LogicQueue.download_thread[i].daemon = True  
                LogicQueue.download_thread[i].start()

        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def download_thread_function(idx):
        while True:
            try:
                entity = LogicQueue.download_queue[idx].get()
                logger.debug('Queue receive item: %s', entity['url'])

                if entity['status'] == '완료':
                    entity['status'] = '중복'
                    entity['index'] = int(entity['total_image_count'])
                    LogicGalleryDL.entity_update('queue_one', entity)
                else:
                    LogicGalleryDL.make_download(entity) 
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
                LogicQueue.download_queue[LogicQueue.static_index % SIZE].put(entity)

            LogicQueue.static_index += 1
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
            for i in range(0, SIZE):
                with LogicQueue.download_queue[i].mutex:
                    LogicQueue.download_queue[i].queue.clear()
            for e in LogicQueue.entity_list:
                if e['status'] not in ['완료', '중복']:
                    ModelGalleryDlItem.delete_by_url(e['url'])
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
                LogicQueue.download_queue[LogicQueue.static_index%SIZE].put(e)
                LogicQueue.static_index += 1
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())