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
from multiprocessing import cpu_count
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

CPU = cpu_count()
SIZE = int(CPU/2) if CPU > 1 else int(CPU)

class LogicQueue(object):
    waiting_queue = []
    download_queue = []
    download_thread = []
    entity_list = []
    cv = threading.Condition()

    @staticmethod
    def queue_start():
        try:
            for i in range(0, SIZE):
                LogicQueue.download_queue.append( Queue.Queue() )
                LogicQueue.download_thread.append( threading.Thread(target=LogicQueue.download_thread_function, args=(i,)) )

            for i in range(0, SIZE):
                LogicQueue.download_thread[i].daemon = True  
                LogicQueue.download_thread[i].start()

            manager = threading.Thread(target=LogicQueue.queue_manager, args=())
            manager.daemon = True
            manager.start()

        except Exception as e: 
            logger.error('[gallery-dl] Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def queue_manager():
        while True:
            try:
                smallest = CPU
                SQ = None
                for i in range(0, SIZE):
                    if LogicQueue.download_queue[i].qsize() < smallest:
                        SQ = LogicQueue.download_queue[i]
                        smallest = LogicQueue.download_queue[i].qsize()
                
                if smallest < 1: # SIZE*1 = 대기 항목 수
                    with LogicQueue.cv:
                        while not len(LogicQueue.waiting_queue):
                            LogicQueue.cv.wait()
                    entity = LogicQueue.waiting_queue.pop(0)
                    LogicQueue.entity_list.append(entity)
                    SQ.put(entity)
                else:
                    import time
                    time.sleep(5)
            except Exception as e:
                logger.error('[gallery-dl] Exception:%s', e)
                logger.error(traceback.format_exc())

    @staticmethod
    def download_thread_function(idx):
        while True:
            try:
                entity = LogicQueue.download_queue[idx].get()
                logger.debug('[gallery-dl] Queue receive item: %s', entity['url'])

                if entity['status'] == '완료':
                    entity['status'] = '중복'
                    entity['index'] = int(entity['total_image_count'])
                    LogicGalleryDL.entity_update('queue_one', entity)
                else:
                    LogicGalleryDL.make_download(entity) 
            except Exception as e: 
                logger.error('[gallery-dl] Exception:%s', e)
                logger.error(traceback.format_exc())

    @staticmethod
    def add_queue(url):
        try:
            entity = ModelGalleryDlItem.add(url)
            if entity is not None:
                for e in LogicQueue.entity_list:
                    if e['url'] == entity['url']:
                        return

                with LogicQueue.cv:
                    LogicQueue.waiting_queue.append(entity)
                    LogicQueue.cv.notify_all()
            return entity
        except Exception as e:
            logger.error('[gallery-dl] Exception:%s', e)
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
            logger.error('[gallery-dl] Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def reset_queue():
        try:
            for e in LogicQueue.waiting_queue:
                ModelGalleryDlItem.delete_by_url(e['url'])

            with LogicQueue.cv:
                LogicQueue.waiting_queue = []
                LogicQueue.cv.notify_all()

            for i in range(0, SIZE):
                with LogicQueue.download_queue[i].mutex:
                    LogicQueue.download_queue[i].queue.clear()
            
            new_list = []
            for e in LogicQueue.entity_list:
                if e['status'] not in ['완료', '중복', '다운로드 중']:
                    ModelGalleryDlItem.delete_by_url(e['url'])
                if e['status'] == '다운로드 중':
                    new_list.append(e)
            LogicQueue.entity_list = new_list

            import plugin
            plugin.send_queue_list()
        except Exception as e:
            logger.error('[gallery-dl] Exception:%s', e)
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
            with LogicQueue.cv:
                for e in failed_list:
                    LogicQueue.waiting_queue.append(e)
                LogicQueue.cv.notify_all()
        except Exception as e:
            logger.error('[gallery-dl] Exception:%s', e)
            logger.error(traceback.format_exc())