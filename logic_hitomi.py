# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
from datetime import datetime
import sys
import string
from subprocess import PIPE, Popen, STDOUT
import threading
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
  
  stop = False

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
      #bundlejsonurl = 'http://k123s456h.pythonanywhere.com/h_data/info.json'
      res = LogicHitomi.get_response(bundlejsonurl)
      bundle_json = json.loads(res) 
      return bundle_json
    except Exception as e:
      logger.error('[gallery-dl] Exception:%s', e)
      logger.error(traceback.format_exc())

  @staticmethod
  def download_json():
    try:
      def down(name, url):
        logger.debug("[gallery-dl] downloading %s", name)
        urllib.urlretrieve(url, os.path.join(LogicHitomi.basepath, name))

      for filename in os.listdir(LogicHitomi.basepath):
        file_path = os.path.join(LogicHitomi.basepath, filename)
        try:
          os.remove(file_path)
        except:
          pass
      
      logger.debug("[gallery-dl] downloading hitomi json files")
      ModelSetting.set('hitomi_data_status', 'pending')

      bundle_json = LogicHitomi.bundlejson()
      last_num = len(bundle_json['urls'])

      logger.debug("[gallery-dl] json download target 0 to %s", str(last_num-1))
      threads = []
      MAX = 5
      idx = 0
      
      for i in range(0, last_num):
        [name, url] = bundle_json['urls'][i]
        t = threading.Thread(target=down, args=(name, url,))
        t.setDaemon(True)
        threads.append(t)

      while(idx < last_num):
        threads[idx].start()
        if(idx>0 and idx%MAX == 0):
          for t in threads[idx-MAX:idx]:
            t.join()
        idx += 1
        
      for t in threads[idx-MAX:]:
        t.join()

      logger.debug("[gallery-dl] downloading hitomi json files DONE")
      ModelSetting.set('hitomi_data_status', 'done')
      ModelSetting.set('hitomi_last_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
      ModelSetting.set('hitomi_last_num', str(last_num))
    except Exception as e:
      logger.error('[gallery-dl] Exception:%s', e)
      logger.error(traceback.format_exc())
  
  @staticmethod
  def download_json_forbidden():
    '''python 3.6
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
  def trim_condition(condition={}):
    def remove(d, k):
      r = dict(d)
      del r[k]
      return r
    
    for key in condition:
      if len(condition[key]) == 0:
        condition = remove(condition, key)
      elif len(condition[key]) == 1 and len(condition[key][0]) == 0:
        condition = remove(condition, key)
    
    return condition

  @staticmethod
  def is_satisfied(gallery={}, condition={}, condition_negative={}):
    # condition: { key1:[val1], key2:[val2] }
    # gallery:
    # type, l, n, a [],  t [],  p [], g [], c []
    # condition:
    # type [], l [], n [], a [],  t [],  p [], g [], c []

    import json

    condition = LogicHitomi.trim_condition(condition)
    condition_negative = LogicHitomi.trim_condition(condition_negative)

    for key, value in condition.items():
      key = key.encode('utf-8')

      if key not in gallery:
        return False
      if gallery[key] is None:
        return False
      if len(gallery[key]) < 1:
        return False

      try:
        # OR
        # artists, group, characters, parody
        if key in ['a', 'g', 'c', 'p']:

          tmp = False
          for condition_value in value:
            if condition_value in gallery[key]:
              tmp = True
              break
          if tmp == False:
            return False
        
        # OR for string
        # type, language
        elif key in ['type', 'l']:
          tmp = False
          for condition_value in value:
            if condition_value.strip().lower() == gallery[key].strip().lower():
              tmp = True
              break
          if tmp == False:
            return False

        # AND
        # tags
        elif key in ['t']:
          
          tmp = True
          for gallery_value in gallery[key]:
            if gallery_value not in value:
              tmp = False
              break
          if tmp == False:
            return False
          
        # SUBSTRING with OR
        # name
        elif key in ['n']:
          tmp = False
          for search_name in value:
            if gallery[key].strip().lower().find(search_name) != -1:
              tmp = True
              break
          if tmp == False:
            return False
        

      except Exception as e:
        logger.debug("[gallery-dl] Exception at: %s %s", type(gallery[key]) ,str(gallery[key]))
        logger.error('[gallery-dl] Exception:%s', e)
        logger.error(traceback.format_exc())


    for key, value in condition_negative.items():
      key = key.encode('utf-8')

      if key not in gallery:
        continue
      if gallery[key] is None:
        continue

      for ban_value in value:
        for gallery_value in gallery[key]:
          if ban_value.strip().lower() in gallery_value.strip().lower():
            return False

      # # AND
      # # artists, tags, parody, group, characters, 
      # if key in ['a', 't', 'p', 'g', 'c']:

      #   for gallery_value in gallery[key]:
      #     for condition_value in value:
      #       if condition_value.strip().lower() in gallery_value.strip().lower():
      #         return False
      # else:
      #   if gallery[key].strip().lower() not in value:
      #     return False

    return True

  @staticmethod
  def thumbnail_url(galleryid):
    # 'https://ltn.hitomi.la/galleries/1692965.js'
    gallery_info_url = 'https://ltn.hitomi.la/galleries/'+ str(galleryid) +'.js'
    try:
      gallery_info = requests.get(gallery_info_url).text[18:]
      info_json = json.loads(gallery_info)
      
      def url_from_url_from_hash(galleryid, image, dir=None, ext=None, base=None):
        extension = image['name'].split('.')[-1]
        if dir is not None and len(dir) != 0:
            extension = dir
        if ext is not None and len(ext) != 0:
            extension = ext
        
        subdir = 'images'
        if dir is not None and len(dir) != 0:
            subdir = dir

        hash = image['hash']
        hash_1 = ''
        hash_2 = ''
        full_path = hash
        if len(hash) >= 3:
            hash_1 = hash[-1]
            hash_2 = hash[-3:-1]
            full_path = hash_1 + '/' + hash_2 + '/' + hash

        tmpurl = 'https://a.hitomi.la/'+dir+'/'+full_path+'.'+ext

        subdomain = 'a'
        if base is not None and len(base) != 0:
            subdomain = base
        
        number_of_frontends = 3
        b = 16
        if len(hash_2) > 0:
            m = hash_2
            g = int(m, 16)
            if g < 0x30:
                number_of_frontends = 2
            if g < 0x09:
                g = 1
            
            o = g % number_of_frontends

            subdomain = chr(97 + o) + subdomain

        url = 'https://'+subdomain+'.hitomi.la/'+dir+'/'+full_path+'.'+ext

        return url

      image = info_json['files'][0]
      dir = 'smalltn'
      ext = 'jpg'
      base = 'tn'

      return url_from_url_from_hash(galleryid, image, dir, ext, base)
    except Exception as e:
      logger.error('[gallery-dl] Exception:%s', e)
      logger.error(traceback.format_exc())
      return '#'

  @staticmethod
  def find_gallery(condition, condition_negative, search=False, scheduler=False):
    try:
      # condition: { key1:[val1], key2:[val2] }
      # key:
      # type, id, l, n, a [],  t [],  p [], g [], c []
      # galleries0.json is the latest
      logger.debug("[gallery-dl] manual search positive condition: %s", str(condition))
      logger.debug("[gallery-dl] manual search negative condition: %s", str(condition_negative))
      ret = []
      last_num = int(ModelSetting.get('hitomi_last_num'))

      for num in range(0, last_num):
        item = "galleries" + str(num) + ".json"
        with open(os.path.join(LogicHitomi.basepath, item)) as galleries:
          json_item = json.loads(galleries.read())

          for _, gallery in enumerate(json_item):
            if ( LogicHitomi.stop == True ) and ( scheduler == False ):
              galleries.close()
              return ret
            
            try:
              if LogicHitomi.is_satisfied(gallery, condition, condition_negative):
                gallery['thumbnail'] = LogicHitomi.thumbnail_url(gallery['id'])
                gallery['url'] = LogicHitomi.baseurl + str(gallery['id']) + '.html'
                logger.debug('[gallery-dl] found item: %s', gallery['id'])

                if search == True:
                  from .plugin import send_search_one
                  send_search_one(gallery)
                
                if scheduler == True:
                  from logic_queue import LogicQueue
                  import plugin
                  LogicQueue.add_queue(gallery['url'])
                  plugin.socketio_callback('queue_one', gallery, encoding=False)

                
                ret.append(gallery)
            except Exception as e:
              import traceback
              logger.error('[gallery-dl] Exception:%s', e)
              logger.error(traceback.format_exc())
              # no such key for this item
          galleries.close()
      return ret
    except Exception as e:
      logger.error('[gallery-dl] Exception:%s', e)
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
      logger.error('[gallery-dl] Exception:%s', e)
      logger.error(traceback.format_exc())


  @staticmethod
  def search(arg):
    LogicHitomi.stop = False
    try:
      condition = {}
      condition['n'] = arg['n'].split('||')
      condition['a'] = arg['a'].split('||')
      condition['g'] = arg['g'].split('||')
      condition['t'] = arg['t'].split('||')
      condition['type'] = arg['type'].split('||')
      condition['c'] = arg['c'].split('||')
      condition['l'] = arg['l'].split('||')
      
      condition_negative={}
      condition_negative['n'] = ModelSetting.get('b_title').split('||')
      condition_negative['a'] = ModelSetting.get('b_artist').split('||')
      condition_negative['g'] = ModelSetting.get('b_group').split('||')
      condition_negative['t'] = ModelSetting.get('b_tags').split('||')
      condition_negative['type'] = ModelSetting.get('b_type').split('||')
      condition_negative['c'] = ModelSetting.get('b_character').split('||')
      condition_negative['l'] = ModelSetting.get('b_language').split('||')

      def func(condition_positive, condition_negative):
        ret = LogicHitomi.find_gallery(condition, condition_negative, search=True)
        # from .plugin import send_search_result
        # send_search_result(ret)

      t = threading.Thread(target=func, args=(condition, condition_negative))
      t.setDaemon(True)
      t.start()

    except Exception as e:
      logger.error('[gallery-dl] Exception:%s', e)
      logger.error(traceback.format_exc())


  @staticmethod
  def scheduler_function():
      logger.debug('[gallery-dl] scheduler hitomi Start')
      try:
        condition_positive = {}
        condition_negative = {}

        condition_positive['n'] = ModelSetting.get('p_title').split('||')
        condition_positive['a'] = ModelSetting.get('p_artist').split('||')
        condition_positive['g'] = ModelSetting.get('p_group').split('||')
        condition_positive['t'] = ModelSetting.get('p_tags').split('||')
        condition_positive['type'] = ModelSetting.get('p_type').split('||')
        condition_positive['c'] = ModelSetting.get('p_character').split('||')
        condition_positive['l'] = ModelSetting.get('p_language').split('||')

        condition_negative['n'] = ModelSetting.get('b_title').split('||')
        condition_negative['a'] = ModelSetting.get('b_artist').split('||')
        condition_negative['g'] = ModelSetting.get('b_group').split('||')
        condition_negative['t'] = ModelSetting.get('b_tags').split('||')
        condition_negative['type'] = ModelSetting.get('b_type').split('||')
        condition_negative['c'] = ModelSetting.get('b_character').split('||')
        condition_negative['l'] = ModelSetting.get('b_language').split('||')

        def func(condition_positive, condition_negative):
          LogicHitomi.find_gallery(condition_positive, condition_negative, scheduler=True)

        t = threading.Thread(target=func, args=(condition_positive, condition_negative))
        t.setDaemon(True)
        t.start()
      except Exception as e:
        logger.error('[gallery-dl] Exception:%s', e)
        logger.error(traceback.format_exc())


'''
    try:
      pass
    except Exception as e:
      logger.error('Exception:%s', e)
      logger.error(traceback.format_exc())
'''