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
from framework import db, scheduler, path_data
from framework.job import Job
from framework.util import Util

# 패키지
import system
from .plugin import package_name, logger
from .model import ModelSetting
from .logic_gallerydl import LogicGalleryDL


#########################################################

class QueueEntity:
    static_index = 0
    entity_list = []

    def __init__(self):
        self.category = ''
        self.title = ''
        self.artist = ''
        self.parody = ''
        #self.all_download = False
        self.episodes = []
        self.static_index = QueueEntity.static_index
        self.index = 0
        self.url = ''
        self.total_image_count = 0
        self.status = '대기'
        QueueEntity.static_index += 1
        QueueEntity.entity_list.append(self)

    def as_dict(self):
        d = {
            'static_index' : self.static_index,
            'index': self.index,
            'category': self.category,
            'title' : self.title,
            'artist' : self.artist,
            'parody': self.parody,
            'episodes' : [x.as_dict() for x in self.episodes],
            'url' : self.url, 
            'total_image_count': self.total_image_count,
            'status' : self.status,
        }
        return d

    def toJSON(self):
        #return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)


    @staticmethod
    def create(url):
        if url is not None:
            for e in QueueEntity.entity_list:
                if e.url == url: # already exists
                    return None

            entity = QueueEntity()
            entity.url = url
            return entity

    # def add(self, url):
    #     e = QueueEntityEpisode()
    #     e.title = self.title
    #     e.artist = self.artist
    #     e.url = self.url
    #     e.index = len(self.episodes)
    #     e.queue_index = self.index
    #     self.episodes.append(e)


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
    def plugin_unload():
        try:
            logger.debug('%s plugin_unload', package_name)
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


    @staticmethod
    def download_thread_function():
        while True:
            try:
                entity = LogicQueue.download_queue.get()
                logger.debug('Queue receive item: %s', entity.url)
                LogicGalleryDL.download(entity)    # TODO: 여기서 다운로드
                LogicQueue.download_queue.task_done()    
            except Exception as e: 
                logger.error('Exception:%s', e)
                logger.error(traceback.format_exc())

    @staticmethod
    def add_queue(url):
        try:
            entity = QueueEntity.create(url)
            if entity is not None:
                LogicQueue.download_queue.put(entity)
        except Exception as e:
            logger.error('Exception: %s', e)
            logger.error(traceback.format_exc())

    
    @staticmethod
    def completed_remove():
        try:
            new_list = []
            for e in QueueEntity.entity_list:
                if e.status not in ['완료', '중복']:
                    new_list.append(e)
            QueueEntity.entity_list = new_list
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
            QueueEntity.entity_list = []
            import plugin
            plugin.send_queue_list()
            LogicNormal.stop()
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


