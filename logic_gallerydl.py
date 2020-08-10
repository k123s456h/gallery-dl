# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import requests
from datetime import datetime
import sys
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
    from fake_useragent import UserAgent
except:
    requirements = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'requirements.txt')
    if os.system('python -m pip install -r %s' % (requirements)) != 0:
        os.system('wget https://bootstrap.pypa.io/get-pip.py')
        os.system('python get-pip.py' % python)
        os.system('python -m pip install -r %s' % (requirements))
from fake_useragent import UserAgent
#########################################################

class LogicGalleryDL:
  stop_flag = False

  @staticmethod
  @celery.task(bind=True)
  def make_download(self, entity):
    try:
      entity['status'] = '메타데이터 수집 중'
      entity['index'] = 0
      LogicGalleryDL.update_ui(self, entity)

      url = entity['url']
      [return_code, info_json] = LogicGalleryDL.get_info_json(url)
      if return_code != 0:
        if 'No suitable extractor' in info_json:
          entity['status'] = '실패: url'
        elif 'SSLError' in info_json or 'ProxyError' in info_json:
          entity['status'] = '실패: proxy'
        else:
          entity['status'] = '실패'

        LogicGalleryDL.update_ui(self, entity)
        return False
      else:
        info_json_directory = info_json['directory']
        info_json_filename = info_json['filename']

        site = info_json['directory']['category']
        entity['category'] = site

        if site == 'hitomi':
          (entity['title'], entity['artist'], entity['parody'], entity['total_image_count']) = \
          (info_json_directory['title'], str(info_json_directory['artist[]']), str(info_json_directory['parody[]']), info_json_directory['count'])
        elif site == 'e-hentai' or site == 'exhentai':
          artist = []
          parody = []

          for tag in info_json_directory['tags[]']:
            if tag.startswith('artist'):
              artist.append(tag[7:])
            elif tag.startswith('parody'):
              parody.append(tag[7:])

          (entity['title'], entity['artist'], entity['parody'], entity['total_image_count']) = \
          (info_json_directory['title'], str(artist), str(parody), info_json_directory['count'])
        elif site == 'mangahere':
          (entity['title'], entity['total_image_count']) = \
          (info_json_directory['manga'], info_json_directory['count'])
        else:
          entity['title'] = info_json_directory['title'] if 'title' in info_json_directory else info_json_directory['manga']
          entity['count'] = info_json_directory['count'] if 'count' in info_json_directory else ''
        
        entity['status'] = '다운로드 중'
        LogicGalleryDL.update_ui(self, entity)
        # logger.debug("%s\n%s\n%s\n%s\n%s", entity['url'], entity['title'], entity['status'], entity['index'], entity['id'])

        user_agent = UserAgent(verify_ssl=False).random
        index = 0
        try:
          commands = ['gallery-dl', url, 
                    '--ignore-config',
                    '--config', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gallery-dl.conf'),
                    '--option', 'extractor.user-agent='+user_agent]
          proc = Popen(commands, stdout=PIPE, stderr=STDOUT)
          for line in iter(proc.stdout.readline, b''):
            index += 1
            entity['index'] = index
            LogicGalleryDL.update_ui(self, entity)
            # logger.debug("line: %s", line)
        except Exception as e:
          logger.error('Exception:%s', e)
          logger.error(traceback.format_exc())

        entity['status'] = '완료'
        entity['index'] = int(entity['total_image_count'])
        LogicGalleryDL.update_ui(self, entity)
        ModelGalleryDlItem.save_as_dict(entity)
        return True
    except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

  @staticmethod
  def get_info_json(url):
    raw_info = ''
    try:
      import subprocess
      commands = ['gallery-dl', url,
      '--ignore-config',
      '--config', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gallery-dl.conf'),
      '--simulate', '--list-keywords']
      raw_info = subprocess.check_output(commands, stderr=subprocess.STDOUT).decode('utf-8')

      info_json = {}

      raw_info = raw_info[raw_info.find('Keywords for directory names:'):]
      raw_info = raw_info.split('\n')
      n = len(raw_info)

      keyword_type = ""
      keyword_name = ""
      keyword = ""
      for idx in range(0, n):
          if raw_info[idx].startswith('['):
              continue
          elif raw_info[idx] == "Keywords for directory names:":
              info_json["directory"] = {}
              keyword_type = "directory"
              continue
          elif raw_info[idx] == "Keywords for filenames and --filter:":
              info_json["filename"] = {}
              keyword_type = "filename"
              continue
          elif raw_info[idx].startswith("-------------"):
            continue
          elif len(raw_info[idx]) == 0:
            continue

          if not raw_info[idx].startswith(' '):
              if raw_info[idx].endswith('[]'):
                keyword = []
              else:
                keyword = ""
              keyword_name = raw_info[idx].strip().decode('utf-8')
              info_json[keyword_type][keyword_name] = keyword
          else:
            if keyword == "":
              info_json[keyword_type][keyword_name] = raw_info[idx].strip().decode('utf-8')
            else:
              info_json[keyword_type][keyword_name].append(raw_info[idx][4:].strip().decode('utf-8'))
      
      # logger.debug("%s info: %s", url, info_json)
      return [0, info_json]
    except Exception as e:
      logger.error('Exception:%s', e)
      logger.error(traceback.format_exc())
      logger.error('Exception: gallery-dl output: %s', raw_info)
      return [-1, raw_info]

  @staticmethod
  def entity_update(cmd, entity):
      import plugin
      plugin.socketio_callback(cmd, entity, encoding=False)
  
  @staticmethod
  def update(arg):
      # logger.debug('FOR update : %s' % arg)
      if arg['status'] == 'PROGRESS':
        entity = arg['result']['data']
        LogicGalleryDL.entity_update('queue_one', entity)
        from .logic_queue import LogicQueue
        for idx, e in enumerate(LogicQueue.entity_list):
          if e['url'] == entity['url']:
              LogicQueue.entity_list[idx] = entity
              break

  @staticmethod
  def update_ui(celery_is, entity):
      if app.config['config']['use_celery']:
          celery_is.update_state(state='PROGRESS', meta={'data':entity})
      else:
          LogicGalleryDL.entity_update('queue_one', entity)

  @staticmethod
  def download(entity):
      if entity['url'].strip() == '':
        return False
      LogicGalleryDL.stop_flag = False
      try:
        if LogicGalleryDL.stop_flag == True:
          return

        LogicGalleryDL.entity_update('queue_one', entity)

        if app.config['config']['use_celery']:
          #result.get()
          try:
              result = LogicGalleryDL.make_download.apply_async((entity,))
              result.get(on_message=LogicGalleryDL.update, propagate=True)
          except:
              logger.debug('CELERY on_message not process.. start with no CELERY')
              LogicGalleryDL.make_download(None, entity)
              LogicGalleryDL.entity_update('queue_one', entity)
        else:
          LogicGalleryDL.make_download(None, entity)
          LogicGalleryDL.entity_update('queue_one', entity)
      except Exception as e: 
              logger.error('Exception:%s', e)
              logger.error(traceback.format_exc())

  @staticmethod
  def scheduler_function():
      from logic_queue import LogicQueue
      logger.debug('gallery-dl scheduler normal Start')
      try:
          downlist = ModelSetting.get('downlist_normal')
          downlist = downlist.split('\n')
          for url in downlist:
            url = url.strip()
            if len(url) > 0:
              LogicQueue.add_queue(url)
          
          import plugin
          plugin.send_queue_list()
      except Exception as e:
          logger.error('Exception:%s', e)
          logger.error(traceback.format_exc())