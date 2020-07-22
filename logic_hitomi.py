# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import requests
from datetime import datetime
import sys
import string
from subprocess import PIPE, Popen, STDOUT

# third-party

# sjva 공용
from framework import app, db, scheduler, path_app_root, celery, SystemModelSetting
from framework.util import Util

# 패키지
from .plugin import logger, package_name
from .model import ModelSetting, ModelGalleryDlItem

#########################################################
try:
    import requests
    from fake_useragent import UserAgent
except:
    requirements = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'requirements.txt')
    if os.system('python -m pip install -r %s' % (requirements)) != 0:
        os.system('wget https://bootstrap.pypa.io/get-pip.py')
        os.system('python get-pip.py' % python)
        os.system('python -m pip install -r %s' % (requirements))
import requests
from fake_useragent import UserAgent
#########################################################

headers = {
                'User-Agent': UserAgent(cache=False).random,
                'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language' : 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
            } 

class LogicHitomi:
  @staticmethod
  def get_response(url):
    try:
      return requests.get(url,headers=headers).text.decode('utf-8')
    except Exception as e:
      logger.error('Exception:%s', e)
      logger.error(traceback.format_exc())
  
  @staticmethod
  def bundlejson():
    try:
      bundlejsonurl = 'https://kurtbestor.pythonanywhere.com/h_data'
      res = get_response(bundlejsonurl).replace("'", '"')
      bundle_json = json.loads(res) 
      return bundle_json
    except Exception as e:
      logger.error('Exception:%s', e)
      logger.error(traceback.format_exc())

  @staticmethod
  def download_json():
    try:
      bundle_json = bundlejson()
      for [name, url] in bundle_json["urls"]:
        print(name, url)
      pass
    except Exception as e:
      logger.error('Exception:%s', e)
      logger.error(traceback.format_exc())


LogicHitomi.download_json()

'''
    try:
      pass
    except Exception as e:
      logger.error('Exception:%s', e)
      logger.error(traceback.format_exc())
'''