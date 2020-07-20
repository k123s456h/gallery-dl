# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import requests
from datetime import datetime
import sys

from subprocess import PIPE, Popen
from Queue import Queue, Empty  # python 2.x

# third-party

# sjva 공용
from framework import app, db, scheduler, path_app_root, celery, SystemModelSetting
from framework.util import Util

# 패키지
from .plugin import logger, package_name
from .model import ModelSetting

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
  def make_process(url): # TODO: 비동기적으로 명령어 실행 및 stdout 가져오기
    try:
      ON_POSIX = 'posix' in sys.builtin_module_names

      user_agent = UserAgent(cache=False).random
      commands = ['gallery-dl', url, 
                '--ignore-config',
                '--config', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gallery-dl.conf'),
                '--option', 'extractor.user-agent='+user_agent]
      
      def enqueue_output(out, queue):
          for line in iter(out.readline, b''):
              queue.put(line)
          out.close()

      p = Popen(commands, stdout=PIPE, bufsize=1, close_fds=ON_POSIX)
      q = Queue()
      t = Thread(target=enqueue_output, args=(p.stdout, q))
      t.daemon = True # thread dies with the program
      t.start()

      # read line without blocking
      try:  line = q.get_nowait() # or q.get(timeout=.1)
      except Empty:
          print('no output yet')
      else: # got line
          print(line)
          # ... do something with line

      return True
    except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

  @staticmethod
  def download(req):
      try:
          url = req.form['url']
          url = None if url == '' else url

          if url is not None:
              LogicGalleryDL.make_process(url)
      except Exception as e: 
              logger.error('Exception:%s', e)
              logger.error(traceback.format_exc())

  @staticmethod
  def get_info_json(url):
      import subprocess
      commands = ['gallery-dl', url, '--ignore-config', '--simulate', '--list-keywords']
      raw_info = subprocess.check_output(commands)

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








'''
https://hitomi.la/galleries/686095.html
Keywords for directory names:
-----------------------------
artist[]
  - Kimimaru
category
  hitomi
characters[]
  - Asuka Langley Soryu
  - Misato Katsuragi
  - Rei Ayanami
  - Ritsuko Akagi
  - Ryoji Kaji
  - Shinji Ikari
count
  107
date
  2014-03-22 04:23:00
gallery_id
  686095
group[]
  - Studio Kimigabuchi
lang
  ko
language
  Korean
parody[]
  - Neon Genesis Evangelion
subcategory
  gallery
tags[]
  - Schoolboy Uniform ♂
  - Multi-work Series
title
  RE-TAKE 1
type
  Doujinshi

Keywords for filenames and --filter:
------------------------------------
artist[]
  - Kimimaru
category
  hitomi
characters[]
  - Asuka Langley Soryu
  - Misato Katsuragi
  - Rei Ayanami
  - Ritsuko Akagi
  - Ryoji Kaji
  - Shinji Ikari
count
  107
date
  2014-03-22 04:23:00
extension
  jpg
filename
  RE_TAKE_0001
gallery_id
  686095
group[]
  - Studio Kimigabuchi
lang
  ko
language
  Korean
num
  1
parody[]
  - Neon Genesis Evangelion
subcategory
  gallery
tags[]
  - Schoolboy Uniform ♂
  - Multi-work Series
title
  RE-TAKE 1
type
  Doujinshi

https://e-hentai.org/g/686095/4873b506a3/
[exhentai][info] no username given; using e-hentai.org
Keywords for directory names:
-----------------------------
category
  exhentai
count
  107
date
  2014-03-22 04:23:00
gallery_id
  686095
gallery_size
  38818284
gallery_token
  4873b506a3
lang
  ko
language
  Korean
parent
  
subcategory
  gallery
tags[]
  - language:korean
  - language:translated
  - parody:neon+genesis+evangelion
  - character:asuka+langley+soryu
  - character:misato+katsuragi
  - character:rei+ayanami
  - character:ritsuko+akagi
  - character:ryoji+kaji
  - character:shinji+ikari
  - group:studio+kimigabuchi
  - artist:kimimaru
  - male:schoolboy+uniform
  - multi-work+series
title
  (C66) [Studio Kimigabuchi (Kimimaru)] RE-TAKE (Neon Genesis Evangelion) [Korean]
title_jp
  (C66) [スタジオKIMIGABUCHI (きみまる)] RE-TAKE (新世紀エヴァンゲリオン) [韓国翻訳]
visible
  Yes

Keywords for filenames and --filter:
------------------------------------
category
  exhentai
cost
  1
count
  107
date
  2014-03-22 04:23:00
extension
  jpg
filename
  RE_TAKE_0001
gallery_id
  686095
gallery_size
  38818284
gallery_token
  4873b506a3
height
  1400
image_token
  4880bfc4de
lang
  ko
language
  Korean
num
  1
parent
  
size
  351848
subcategory
  gallery
tags[]
  - language:korean
  - language:translated
  - parody:neon+genesis+evangelion
  - character:asuka+langley+soryu
  - character:misato+katsuragi
  - character:rei+ayanami
  - character:ritsuko+akagi
  - character:ryoji+kaji
  - character:shinji+ikari
  - group:studio+kimigabuchi
  - artist:kimimaru
  - male:schoolboy+uniform
  - multi-work+series
title
  (C66) [Studio Kimigabuchi (Kimimaru)] RE-TAKE (Neon Genesis Evangelion) [Korean]
title_jp
  (C66) [スタジオKIMIGABUCHI (きみまる)] RE-TAKE (新世紀エヴァンゲリオン) [韓国翻訳]
visible
  Yes
width
  990


    @staticmethod
    def make_process(url):
        try:
            pass
        except Exception as e: 
                logger.error('Exception:%s', e)
                logger.error(traceback.format_exc())
'''