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

  @staticmethod
  def make_download(entity):
    try:
      entity['status'] = '메타데이터 수집 중'
      entity['index'] = 0
      LogicGalleryDL.update_ui(entity)

      url = entity['url']
      [return_code, info_json] = LogicGalleryDL.get_info_json(url)
      if return_code != 0:
        if 'exit status 64' in info_json:
          entity['status'] = '실패: url'
        elif 'exit status 4' in info_json:
          entity['status'] = '실패: 차단된 사이트'
        else:
          entity['status'] = '실패'

        LogicGalleryDL.update_ui(entity)
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
        LogicGalleryDL.update_ui(entity)
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
            LogicGalleryDL.update_ui(entity)
            logger.debug("gallery-dl: %s", line[:-1])
        except Exception as e:
          logger.error('Exception:%s', e)
          logger.error(traceback.format_exc())
          entity['status'] = '실패'
          LogicGalleryDL.update_ui(entity)
          return False

        entity['status'] = '완료'
        entity['index'] = int(entity['total_image_count'])
        LogicGalleryDL.update_ui(entity)
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
      logger.error('Exception at: %s', url)
      logger.error(traceback.format_exc())
      return [-1, str(e)]

  @staticmethod
  def entity_update(cmd, entity):
      import plugin
      plugin.socketio_callback(cmd, entity, encoding=False)
  

  @staticmethod
  def update_ui(entity):
    from plugin import send_queue_list
    send_queue_list()
    LogicGalleryDL.entity_update('queue_one', entity)
        


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


''' test cases
https://www.mangahere.cc/manga/mahoroba_kissa/c019
https://www.mangahere.cc/manga/mahoroba_kissa/c018
https://www.mangahere.cc/manga/mahoroba_kissa/c017
https://www.mangahere.cc/manga/mahoroba_kissa/c016
https://www.mangahere.cc/manga/mahoroba_kissa/c015
https://www.mangahere.cc/manga/mahoroba_kissa/c014
https://www.mangahere.cc/manga/mahoroba_kissa/c013
https://www.mangahere.cc/manga/mahoroba_kissa/c012
https://www.mangahere.cc/manga/mahoroba_kissa/c011
https://www.mangahere.cc/manga/mahoroba_kissa/c010
'''