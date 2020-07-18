# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import requests
from datetime import datetime

# third-party

# sjva 공용
from framework import app, db, scheduler, path_app_root, celery, SystemModelSetting
from framework.util import Util

# 패키지
from .plugin import logger, package_name
from .model import ModelSetting

#########################################################

class LogicHitomi(object):
    h_json_url = 'https://kurtbestor.pythonanywhere.com/h_data'
    # h_json_path = '/app/data/custom/gallery-dl/hitomi-data'
    h_json_path = '/app/data/plugin/gallery-dl/hitomi-data' # for dev

    @staticmethod
    def download_json():
        try:
            pass
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())


  '''
    @staticmethod
    def make_process(url):
        try:
            pass
        except Exception as e: 
                logger.error('Exception:%s', e)
                logger.error(traceback.format_exc())
'''