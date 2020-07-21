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
      entity.status = '다운로드 중'
      LogicGalleryDL.entity_update('change_status', entity.as_dict())

      url = entity.url

      info_json = LogicGalleryDL.get_info_json(url)
      if info_json == "invalid":
        entity.status='실패: url'
        LogicGalleryDL.entity_update('change_status', entity.as_dict())
        return False
      else:
        info_json_directory = info_json['directory']
        info_json_filename = info_json['filename']

        site = info_json['directory']['category']
        entity.category = site
        if site == 'hitomi':
          (entity.title, entity.artist, entity.parody, entity.total_image_count) = \
          (info_json_directory['title'], str(info_json_directory['artist[]']), str(info_json_directory['parody[]']), info_json_directory['count'])
        elif site == 'e-hentai' or site == 'exhentai':
          artist = []
          parody = []

          for tag in info_json_directory['tags[]']:
            if tag.startswith('artist'):
              artist.append(tag[7:])
            elif tag.startswith('parody'):
              parody.append(tag[7:])

          (entity.title, entity.artist, entity.parody, entity.total_image_count) = \
          (info_json_directory['title'], str(artist), str(parody), info_json_directory['count'])
        elif site == 'mangahere':
          (entity.title, entity.total_image_count) = \
          (info_json_directory['manga'], info_json_directory['count'])
        else:
          pass
        
        LogicGalleryDL.entity_update('change_status', entity.as_dict())
        logger.debug("%s\n%s\n%s\n%s\n%s", entity.url, entity.title, entity.artist, entity.parody, entity.total_image_count)

        user_agent = UserAgent(cache=False).random
        try:
          commands = ['gallery-dl', url, 
                    '--ignore-config',
                    '--config', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gallery-dl.conf'),
                    '--option', 'extractor.user-agent='+user_agent]
          proc = Popen(commands, stdout=PIPE, stderr=STDOUT)
          for line in iter(proc.stdout.readline, b''):
            entity.index += 1
            LogicGalleryDL.entity_update('change_status', entity.as_dict())
            logger.debug("line: %s", line)
        except Exception as e:
          logger.error('Exception:%s', e)
          logger.error(traceback.format_exc())

        entity.status = '완료'
        LogicGalleryDL.entity_update('change_status', entity.as_dict())
        ModelGalleryDlItem.save(entity)
        return True
    except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

  @staticmethod
  def get_info_json(url):
    try:
      import subprocess
      commands = ['gallery-dl', url, '--ignore-config', '--simulate', '--list-keywords']
      raw_info = subprocess.check_output(commands, stderr=subprocess.STDOUT).decode('utf-8')

      info_json = {}
      raw_info = raw_info.split('\n')
      n = len(raw_info)

      keyword_type = ""
      keyword_name = ""
      keyword = ""
      for idx in range(0, n):
          if raw_info[idx].startswith('['):
              continue
          if raw_info[idx] == "Keywords for directory names:":
              info_json["directory"] = {}
              keyword_type = "directory"
              continue
          if raw_info[idx] == "Keywords for filenames and --filter:":
              info_json["filename"] = {}
              keyword_type = "filename"
              continue
          if raw_info[idx].startswith("-------------"):
            continue
          if len(raw_info[idx]) == 0:
            continue

          if not raw_info[idx].startswith(' '):
              if raw_info[idx].endswith('[]'):
                keyword = []
              else:
                keyword = ""
              keyword_name = raw_info[idx].strip()
              info_json[keyword_type][keyword_name] = keyword
          else:
            if keyword == "":
              info_json[keyword_type][keyword_name] = raw_info[idx].strip()
            else:
              info_json[keyword_type][keyword_name].append(raw_info[idx][4:].strip())
      return info_json
    except Exception as e:
      logger.error('Exception: returncode: %s', e.returncode)
      logger.error('Exception: output:     %s', e.output)
      return "invalid"

  @staticmethod
  def entity_update(cmd, entity):
      import plugin
      # 'queue_one' ''change_status''
      plugin.socketio_callback(cmd, entity, encoding=False)

  @staticmethod
  def download(entity):
      LogicGalleryDL.stop_flag = False
      try:
          url = entity.url
          url = None if url == '' else url
          if url is not None:
              if LogicGalleryDL.stop_flag == True:
                return

              LogicGalleryDL.entity_update('queue_one', entity.as_dict())

              is_in_completed_list = ModelGalleryDlItem.get(entity.url)
              if is_in_completed_list is None:

                  if app.config['config']['use_celery']:
                      isSuccess = LogicGalleryDL.make_download.apply_async((entity,)).get()
                      # if isSuccess:
                      #   LogicGalleryDL.update(entity)
                      # else:
                      #   LogicGalleryDL.entity_update(entity)
                      LogicGalleryDL.entity_update('change_status', entity.as_dict())
                  else:
                    LogicGalleryDL.make_download(None, entity)

              else:
                  entity.status = '중복'  
          else:
              entity.status='실패: url'

          LogicGalleryDL.entity_update('change_status', entity.as_dict())
      except Exception as e: 
              logger.error('Exception:%s', e)
              logger.error(traceback.format_exc())