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
      #bundlejsonurl = 'https://kurtbestor.pythonanywhere.com/h_data'
      bundlejsonurl = 'http://k123s456h.pythonanywhere.com/h_data/info.json'
      res = LogicHitomi.get_response(bundlejsonurl)
      bundle_json = json.loads(res) 
      return bundle_json
    except Exception as e:
      logger.error('Exception:%s', e)
      logger.error(traceback.format_exc())

  @staticmethod
  def download_json():
    try:
      logger.debug("### gallery-dl: downloading hitomi json file")

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
    import json

    condition = LogicHitomi.trim_condition(condition)
    condition_negative = LogicHitomi.trim_condition(condition_negative)

    for key, value in condition.items():  # AND
      key = key.encode('utf-8')

      if key not in gallery:
        return False
      if gallery[key] is None:
        return False

      try:
        if key in ['a', 't', 'p', 'g', 'c']:

          for condition_value in value:
            tmp = False
            for gallery_value in gallery[key]:
              if condition_value.strip().lower() in gallery_value.strip().lower():
                tmp = True
            if tmp == False:
              return False

        else:
          if gallery[key].strip().lower() not in value:
            return False
      except Exception as e:
        logger.debug("Exception at: %s %s", type(gallery[key]) ,str(gallery[key]))
        logger.error('Exception:%s', e)
        logger.error(traceback.format_exc())


    for key, value in condition_negative.items(): # OR
      key = key.encode('utf-8')

      if key not in gallery:
        continue
      if gallery[key] is None:
        continue

      if key in ['a', 't', 'p', 'g', 'c']:

        for condition_value in value:
          for gallery_value in gallery[key]:
            if condition_value.strip().lower() in gallery_value.strip().lower():
              return False

      else:
        if gallery[key].strip().lower() not in value:
          return False

    return True


  @staticmethod
  def find_gallery(condition, condition_negative):
    try:
      # condition: { key1:[val1], key2:[val2] }
      # key:
      # type, id, l, n, a [],  t [],  p [], g [], c []
      # galleries0.json is the latest
      logger.debug("search condition: %s", str(condition))

      ret = []

      last_num = int(ModelSetting.get('hitomi_last_num'))

      for num in range(0, last_num + 1):
        item = "galleries" + str(num) + ".json"
        with open(os.path.join(LogicHitomi.basepath, item)) as galleries:
          json_item = json.loads(galleries.read())

          for idx, gallery in enumerate(json_item):
            try:
              if LogicHitomi.is_satisfied(gallery, condition, condition_negative):
                gallery['thumbnail'] = ''
                gallery['url'] = LogicHitomi.baseurl + str(gallery['id']) + '.html'
                logger.debug('found item: %s', gallery['n'])
                ret.append(gallery)
            except Exception as e:
              import traceback
              logger.error('Exception:%s', e)
              logger.error(traceback.format_exc())
              # no such key for this item
          galleries.close()
      return ret
    except Exception as e:
      logger.error('Exception:%s', e)
      logger.error(traceback.format_exc())

  @staticmethod
  def return_url(condition, condition_negative):
    urls = []
    galleries = LogicHitomi.find_gallery(condition, condition_negative)
    for gallery in galleries:
      urls.append(gallery['url'])
    return urls

  
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
  def search(req):
    try:
      condition = {}
      condition['n'] = req.form['n'].split('||')
      condition['a'] = req.form['a'].split('||')
      condition['g'] = req.form['g'].split('||')
      condition['t'] = req.form['t'].split('||')
      condition['type'] = req.form['type'].split('||')
      condition['c'] = req.form['c'].split('||')
      condition['l'] = req.form['l'].split('||')
      
      condition_negative={}
      condition_negative['n'] = ModelSetting.get('b_title').split('||')
      condition_negative['a'] = ModelSetting.get('b_artist').split('||')
      condition_negative['g'] = ModelSetting.get('b_group').split('||')
      condition_negative['t'] = ModelSetting.get('b_tags').split('||')
      condition_negative['type'] = ModelSetting.get('b_type').split('||')
      condition_negative['c'] = ModelSetting.get('b_character').split('||')
      condition_negative['l'] = ModelSetting.get('b_language').split('||')

      # logger.debug("search condition: %s", str(condition))

      # ret = []

      # last_num = int(ModelSetting.get('hitomi_last_num'))
      
      # for num in range(0, last_num + 1):
      #   with open(os.path.join(LogicHitomi.basepath, 'galleries'+str(num)+'.json')) as galleries:
      #     import json
      #     json_item = json.loads(galleries.read())

      #     for idx, gallery in enumerate(json_item):
      #       try:
      #         if LogicHitomi.is_satisfied(gallery, condition, condition_negative):
      #           tmp = gallery
      #           tmp['thumbnail'] = ''
      #           tmp['url'] = LogicHitomi.baseurl + str(gallery['id']) + '.html'

      #           ret.append(tmp)

      #           logger.debug('found item: %s', tmp['n'])
      #       except Exception as e:
      #         import traceback
      #         logger.error('Exception:%s', e)
      #         logger.error(traceback.format_exc())
      #         # no such key for this item
          
      #     galleries.close()

      galleries = LogicHitomi.find_gallery(condition, condition_negative)
      
      from .plugin import send_search_result
      send_search_result(galleries)
    except Exception as e:
      logger.error('Exception:%s', e)
      logger.error(traceback.format_exc())



  @staticmethod
  def scheduler_function():
      from logic_queue import LogicQueue
      logger.debug('gallery-dl scheduler hitomi Start')
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

        urls = LogicHitomi.return_url(condition_positive, condition_negative)
        for url in urls:
          # logger.debug('added by scheduler: %s', url)
          LogicQueue.add_queue(url)

        import plugin
        plugin.send_queue_list()
      except Exception as e:
        logger.error('Exception:%s', e)
        logger.error(traceback.format_exc())


'''
    try:
      pass
    except Exception as e:
      logger.error('Exception:%s', e)
      logger.error(traceback.format_exc())
'''
'''
1692965
https://ltn.hitomi.la/galleries/__gallery_num__.js

https://atn.hitomi.la/smalltn/7/0e/38de749c71e2f4eaa901477d510e8c9a506beae3175439707fb9670dfcc9b0e7.jpg
atn, 7, 0e, 해쉬부분은 바뀜



function url_from_url(url, base) {
        return url.replace(/\/\/..?\.hitomi\.la\//, '//'+subdomain_from_url(url, base)+'.hitomi.la/');
}

function url_from_hash(galleryid, image, dir, ext) {
        ext = ext || dir || image.name.split('.').pop();
        dir = dir || 'images';
        
        return 'https://a.hitomi.la/'+dir+'/'+full_path_from_hash(image.hash)+'.'+ext;
}

function url_from_url_from_hash(galleryid, image, dir, ext, base) {
        return url_from_url(url_from_hash(galleryid, image, dir, ext), base);
}

function image_url_from_image(galleryid, image, no_webp) {
        var webp;
        if (image['hash'] && image['haswebp'] && !no_webp) {
                webp = 'webp';
        }
        
        return url_from_url_from_hash(galleryid, image, webp);
}

이미지 주소(webp):
image_url_from_image
image_url_from_image("1693188", {"width":209,"hash":"38de749c71e2f4eaa901477d510e8c9a506beae3175439707fb9670dfcc9b0e7","haswebp":1,"name":"000.jpg","height":300,"hasavif":1}, null)

image정보는 ltn.hitomi.la에서 가져올 수 있음
'''