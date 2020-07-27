# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
from datetime import datetime
import sys
import string
from subprocess import PIPE, Popen, STDOUT
import json
import urllib

# third-party

# sjva 공용
from framework import app, db, scheduler, path_app_root, celery, SystemModelSetting
from framework.util import Util

# 패키지
from .plugin import logger, package_name
from .model import ModelSetting

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

'''
condition
language:["korean"],
artist:["a", "b"]
'''

class LogicHitomi:

  headers = {
                'User-Agent': UserAgent(cache=False).random,
                'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language' : 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
            } 

  baseurl = 'https://hitomi.la/galleries/'
  basepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hitomi-data')
  if not os.path.isdir(basepath):
    os.mkdir(basepath)


  @staticmethod
  def get_response(url):
    try:
      return requests.get(url,headers=LogicHitomi.headers).text.decode('utf-8')
    except Exception as e:
      logger.error('Exception:%s', e)
      logger.error(traceback.format_exc())
  
  @staticmethod
  def bundlejson():
    try:
      bundlejsonurl = 'https://kurtbestor.pythonanywhere.com/h_data'
      res = LogicHitomi.get_response(bundlejsonurl)
      bundle_json = json.loads(res) 
      return bundle_json
    except Exception as e:
      logger.error('Exception:%s', e)
      logger.error(traceback.format_exc())

  @staticmethod
  def download_json():
    try:
      bundle_json = LogicHitomi.bundlejson()

      last_num = ""
      for [name, url] in bundle_json["urls"]:
        urllib.urlretrieve(url, os.path.join(LogicHitomi.basepath, name))
        last_num = name
      last_num = ''.join(x for x in last_num if x.isdigit())
      
      ModelSetting.set('hitomi_last_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
      ModelSetting.set('hitomi_last_num', last_num)
    except Exception as e:
      logger.error('Exception:%s', e)
      logger.error(traceback.format_exc())
  
  @staticmethod
  def download_json_forbidden():
    '''
    html = 'https://kurtbestor.github.io/res/raw.txt' 다운로드 <- 바이트 스트링
    s_b64 = html.replace(' ', '').replace('\n', '').replace('\r', '')
    import base64
    s = base64.decodestring(s_b64) <- zip파일임

    with open(os.path.join(HITOMI_DATA, ZIP_NAME), 'wb') as (f):
        f.write(s)
    with zipfile.ZipFile(os.path.join(HITOMI_DATA, ZIP_NAME), 'r') as (f):
        f.extractall(HITOMI_DATA)
    os.remove(os.path.join(HITOMI_DATA, ZIP_NAME))

    galleries0_forbidden.json
    '''

  
  @staticmethod
  def find_gallery(condition, condition_negative):
    try:
      # condition: { key1:[val1], key2:[val2] }
      # key:
      # type, id, l, n, a [],  t [],  p [], g [], c []
      # galleries0.json is the latest
      ret = []
      if len(condition) == 0:
        return ret

      last_num = int(ModelSetting.get('hitomi_last_num'))

      def parse(value):
        import json
        return json.loads(value)
      
      for num in range(0, last_num + 1):
        item = "galleries" + str(num) + ".json"
        with open(os.path.join(LogicHitomi.basepath, item)) as galleries:
          json_item = json.loads(galleries.read())

          for idx, gallery in enumerate(json_item):
            try:
              flag = True

              for key, value in condition.items():  # AND
                key = key.encode('utf-8')

                if key not in gallery:
                  flag = False
                  break

                if key in ['a', 't', 'p', 'g', 'c']:
                  tmp = False
                  for v in parse(gallery[key]):
                    if v.lower() in value:
                      tmp = True
                      break
                  flag = tmp
                else:
                  if gallery[key].lower() not in value():
                    flag = False
              

              for key, value in condition_negative.items(): # OR
                key = key.encode('utf-8')

                if key not in gallery:
                  continue

                if key in ['a', 't', 'p', 'g', 'c']:
                  for v in parse(gallery[key]):
                    if v.lower() in value:
                      flag = False
                      break
                    break
                else:
                  if gallery[key].lower() not in value:
                    flag = False
                    break
                
              if flag:
                ret.append(gallery)
            except Exception as e:
              import traceback
              print('Exception:%s', e)
              print(traceback.format_exc())
              # no such key for this item
          
          galleries.close()
      
      return ret
    except Exception as e:
      logger.error('Exception:%s', e)
      logger.error(traceback.format_exc())

  @staticmethod
  def return_url(condition, condition_negative):
    urls = []
    galleris = LogicHitomi.find_gallery(condition, condition_negative)
    for gallery in galleris:
      url = LogicHitomi.baseurl + str(gallery['id']) + '.html'
      urls.append(url)
    return urls
  
  @staticmethod
  def scheduler_function():
      from logic_queue import LogicQueue
      logger.debug('gallery-dl scheduler downlist_hitomi Start')
      try:
        condition_positive = {}
        condition_negative = {}

        downlist = ModelSetting.get('downlist_hitomi')
        downlist = downlist.split('\n')
        blacklist = ModelSetting.get('blacklist_hitomi')
        blacklist = blacklist.split('\n')

        condition_positive = LogicHitomi.list_to_dict(downlist)
        condition_negative = LogicHitomi.list_to_dict(blacklist)
        
        urls = return_url(condition_positive, condition_negative)
        for url in urls:
          LogicQueue.add_queue(url)

        import plugin
        plugin.send_queue_list()
      except Exception as e:
        logger.error('Exception:%s', e)
        logger.error(traceback.format_exc())
  
  @staticmethod
  def list_to_dict(condition_list):
    try:
      def parse(value):
        import json
        return json.loads(value)
      ret = {}
      for key_value_string in condition_list:
        [key, value] = key_value_string.split(':')
        if key == 'language': 
          ret['l'] = parse(value)
        elif key == 'artist':
          ret['a'] = parse(value)
        elif key == 'tags':
          ret['t'] = parse(value)
        elif key == 'parody':
          ret['p'] = parse(value)
        elif key == 'type':
          ret['type'] = parse(value)
        elif key == 'group':
          ret['g'] = parse(value)
        elif key == 'character':
          ret['c'] = parse(value)
      return ret
    except Exception as e:
      logger.error('Exception:%s', e)
      logger.error(traceback.format_exc())

  @staticmethod
  def search(condition):
    def remove(d, k):
      r = dict(d)
      del r[k]
      return r
    
    condition = dict(condition)

    for key in condition:
      if len(condition[key].strip()) == 0:
        condition = remove(condition, key)

    ret = []
    galleries = LogicHitomi.find_gallery(condition, [])

    for gallery in galleries:
      tmp = {}
      tmp['thumbnail'] = ''
      tmp['title'] = gallery['n']
      tmp['url'] = LogicHitomi.baseurl + str(gallery['id']) + '.html'
      tmp['tags'] = gallery['t']
      tmp['type'] = gallery['type']
      tmp['parody'] = gallery['p']
      tmp['character'] = gallery['c']
      tmp['artist'] = gallery['a']
      tmp['group'] = gallery['g']
      tmp['language'] = gallery['l']
      ret.append(tmp)

    return ret
'''
["female:ahegao","female:big breasts","female:nakadashi","female:pasties","female:sole female","female:stockings","female:vtuber","group","male:big penis","male:eyemask","mosaic censorship","nijisanji"]

    try:
      pass
    except Exception as e:
      logger.error('Exception:%s', e)
      logger.error(traceback.format_exc())
'''