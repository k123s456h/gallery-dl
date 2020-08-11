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
  
  flag = True

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
      logger.error('Exception:%s', e)
      logger.error(traceback.format_exc())
      return '#'

  @staticmethod
  def find_gallery(condition, condition_negative, search=False, scheduler=False):
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
            if LogicHitomi.flag == False and scheduler == False:
              return ret
            
            try:
              if LogicHitomi.is_satisfied(gallery, condition, condition_negative):
                gallery['thumbnail'] = LogicHitomi.thumbnail_url(gallery['id'])
                gallery['url'] = LogicHitomi.baseurl + str(gallery['id']) + '.html'
                logger.debug('found item: %s', gallery['n'])

                if search == True:
                  from .plugin import send_search_one
                  send_search_one(gallery)
                if scheduler == True:
                  from logic_queue import LogicQueue
                  LogicQueue.add_queue(gallery['url'])
                
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
  def search(arg):
    LogicHitomi.flag = True
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
      logger.error('Exception:%s', e)
      logger.error(traceback.format_exc())


  @staticmethod
  def scheduler_function():
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

        def func(condition_positive, condition_negative):
          LogicHitomi.find_gallery(condition_positive, condition_negative, scheduler=True)

        t = threading.Thread(target=func, args=(condition_positive, condition_negative))
        t.setDaemon(True)
        t.start()
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

"use strict";

var adapose = false;
var loading_timer;
var domain = (/^dev\./.test(document.location.hostname.toString()) ? 'dev' : 'ltn')+'.hitomi.la';
var galleryblockextension = '.html';
var galleryblockdir = 'galleryblock';
var nozomiextension = '.nozomi';

function subdomain_from_galleryid(g, number_of_frontends) {
        if (adapose) {
                return '0';
        }
        
        var o = g % number_of_frontends;

        return String.fromCharCode(97 + o);
}

function subdomain_from_url(url, base) {
        var retval = 'a';
        if (base) {
                retval = base;
        }
        
        var number_of_frontends = 3;
        var b = 16;
        
        var r = /\/[0-9a-f]\/([0-9a-f]{2})\//;
        var m = r.exec(url);
        if (!m) {
                return retval;
        }
        
        var g = parseInt(m[1], b);
        if (!isNaN(g)) {
                if (g < 0x30) {
                        number_of_frontends = 2;
                }
                if (g < 0x09) {
                        g = 1;
                }
                retval = subdomain_from_galleryid(g, number_of_frontends) + retval;
        }
        
        return retval;
}

function url_from_url(url, base) {
        return url.replace(/\/\/..?\.hitomi\.la\//, '//'+subdomain_from_url(url, base)+'.hitomi.la/');
}


function full_path_from_hash(hash) {
        if (hash.length < 3) {
                return hash;
        }
        return hash.replace(/^.*(..)(.)$/, '$2/$1/'+hash);
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
: //ltn.hitomi.la/galleries/1553604.js
https://atn.hitomi.la/smalltn/7/0e/38de749c71e2f4eaa901477d510e8c9a506beae3175439707fb9670dfcc9b0e7.jpg

  url_from_url_from_hash("1566712", {"width":300,"hash":"4616e0234c44ca6748546a4eee701efe88d338e7809a72c81fc0576c9e3f9af3","haswebp":1,"name":"1.jpg","height":241,"hasavif":0}, "webpsmallsmalltn", "webp","tn") -> "//btn.hitomi.la/webpsmallsmalltn/3/af/4616e0234c44ca6748546a4eee701efe88d338e7809a72c81fc0576c9e3f9af3.webp" common.js:70:8
  url_from_url_from_hash("1566712", {"width":300,"hash":"4616e0234c44ca6748546a4eee701efe88d338e7809a72c81fc0576c9e3f9af3","haswebp":1,"name":"1.jpg","height":241,"hasavif":0}, "webpsmalltn", "webp","tn") -> "//btn.hitomi.la/webpsmalltn/3/af/4616e0234c44ca6748546a4eee701efe88d338e7809a72c81fc0576c9e3f9af3.webp" common.js:70:8
  url_from_url_from_hash("1566712", {"width":300,"hash":"4616e0234c44ca6748546a4eee701efe88d338e7809a72c81fc0576c9e3f9af3","haswebp":1,"name":"1.jpg","height":241,"hasavif":0}, "smalltn", "jpg","tn") -> "//btn.hitomi.la/smalltn/3/af/4616e0234c44ca6748546a4eee701efe88d338e7809a72c81fc0576c9e3f9af3.jpg" common.js:70:8
  url_from_url_from_hash("1566712", {"width":300,"hash":"f88d8c37a29d7df775ab478c803970e208ea183049af5ece7b0abfd909f4ff53","haswebp":1,"name":"2.jpg","height":241,"hasavif":0}, "webpsmallsmalltn", "webp","tn") -> "//ctn.hitomi.la/webpsmallsmalltn/3/f5/f88d8c37a29d7df775ab478c803970e208ea183049af5ece7b0abfd909f4ff53.webp" common.js:70:8
  url_from_url_from_hash("1566712", {"width":300,"hash":"f88d8c37a29d7df775ab478c803970e208ea183049af5ece7b0abfd909f4ff53","haswebp":1,"name":"2.jpg","height":241,"hasavif":0}, "webpsmalltn", "webp","tn") -> "//ctn.hitomi.la/webpsmalltn/3/f5/f88d8c37a29d7df775ab478c803970e208ea183049af5ece7b0abfd909f4ff53.webp" common.js:70:8
  url_from_url_from_hash("1566712", {"width":300,"hash":"f88d8c37a29d7df775ab478c803970e208ea183049af5ece7b0abfd909f4ff53","haswebp":1,"name":"2.jpg","height":241,"hasavif":0}, "smalltn", "jpg","tn") -> "//ctn.hitomi.la/smalltn/3/f5/f88d8c37a29d7df775ab478c803970e208ea183049af5ece7b0abfd909f4ff53.jpg" common.js:70:8
  url_from_url_from_hash("1566712", {"width":300,"hash":"692e0ab1eae1184c0a34e5e801e5769c2e80ccd1ac9c62abfec1cc3b32d9d858","haswebp":1,"name":"3.jpg","height":241,"hasavif":0}, "webpsmallsmalltn", "webp","tn") -> "//btn.hitomi.la/webpsmallsmalltn/8/85/692e0ab1eae1184c0a34e5e801e5769c2e80ccd1ac9c62abfec1cc3b32d9d858.webp" common.js:70:8
  url_from_url_from_hash("1566712", {"width":300,"hash":"692e0ab1eae1184c0a34e5e801e5769c2e80ccd1ac9c62abfec1cc3b32d9d858","haswebp":1,"name":"3.jpg","height":241,"hasavif":0}, "webpsmalltn", "webp","tn") -> "//btn.hitomi.la/webpsmalltn/8/85/692e0ab1eae1184c0a34e5e801e5769c2e80ccd1ac9c62abfec1cc3b32d9d858.webp" common.js:70:8
  url_from_url_from_hash("1566712", {"width":300,"hash":"692e0ab1eae1184c0a34e5e801e5769c2e80ccd1ac9c62abfec1cc3b32d9d858","haswebp":1,"name":"3.jpg","height":241,"hasavif":0}, "smalltn", "jpg","tn") -> "//btn.hitomi.la/smalltn/8/85/692e0ab1eae1184c0a34e5e801e5769c2e80ccd1ac9c62abfec1cc3b32d9d858.jpg" common.js:70:8
  url_from_url_from_hash("1566712", {"width":300,"hash":"1070c2c2233886dc3ff0e38afd45ce6c66153118b995379e6f6e39f6410c2cd5","haswebp":1,"name":"4.jpg","height":241,"hasavif":0}, "webpsmallsmalltn", "webp","tn") -> "//btn.hitomi.la/webpsmallsmalltn/5/cd/1070c2c2233886dc3ff0e38afd45ce6c66153118b995379e6f6e39f6410c2cd5.webp" common.js:70:8
  url_from_url_from_hash("1566712", {"width":300,"hash":"1070c2c2233886dc3ff0e38afd45ce6c66153118b995379e6f6e39f6410c2cd5","haswebp":1,"name":"4.jpg","height":241,"hasavif":0}, "webpsmalltn", "webp","tn") -> "//btn.hitomi.la/webpsmalltn/5/cd/1070c2c2233886dc3ff0e38afd45ce6c66153118b995379e6f6e39f6410c2cd5.webp" common.js:70:8
  url_from_url_from_hash("1566712", {"width":300,"hash":"1070c2c2233886dc3ff0e38afd45ce6c66153118b995379e6f6e39f6410c2cd5","haswebp":1,"name":"4.jpg","height":241,"hasavif":0}, "smalltn", "jpg","tn") -> "//btn.hitomi.la/smalltn/5/cd/1070c2c2233886dc3ff0e38afd45ce6c66153118b995379e6f6e39f6410c2cd5.jpg" common.js:70:8
  url_from_url_from_hash("1566712", {"width":300,"hash":"b15aa86f9fb459ec60dd82f8ca142e80ec6d11fe87f8a2db1b2b8e8c47f0f285","haswebp":1,"name":"5.jpg","height":226,"hasavif":0}, "webpsmallsmalltn", "webp","tn") -> "//atn.hitomi.la/webpsmallsmalltn/5/28/b15aa86f9fb459ec60dd82f8ca142e80ec6d11fe87f8a2db1b2b8e8c47f0f285.webp" common.js:70:8
  url_from_url_from_hash("1566712", {"width":300,"hash":"b15aa86f9fb459ec60dd82f8ca142e80ec6d11fe87f8a2db1b2b8e8c47f0f285","haswebp":1,"name":"5.jpg","height":226,"hasavif":0}, "webpsmalltn", "webp","tn") -> "//atn.hitomi.la/webpsmalltn/5/28/b15aa86f9fb459ec60dd82f8ca142e80ec6d11fe87f8a2db1b2b8e8c47f0f285.webp" common.js:70:8
  url_from_url_from_hash("1566712", {"width":300,"hash":"b15aa86f9fb459ec60dd82f8ca142e80ec6d11fe87f8a2db1b2b8e8c47f0f285","haswebp":1,"name":"5.jpg","height":226,"hasavif":0}, "smalltn", "jpg","tn") -> "//atn.hitomi.la/smalltn/5/28/b15aa86f9fb459ec60dd82f8ca142e80ec6d11fe87f8a2db1b2b8e8c47f0f285.jpg" common.js:70:8
  url_from_url_from_hash("1566712", {"width":202,"hash":"152d981622fe31781498da5b1e42963abafda46f7942760baa2e35b06b309976","haswebp":1,"name":"6.jpg","height":300,"hasavif":0}, "webpsmallsmalltn", "webp","tn") -> "//btn.hitomi.la/webpsmallsmalltn/6/97/152d981622fe31781498da5b1e42963abafda46f7942760baa2e35b06b309976.webp" common.js:70:8
  url_from_url_from_hash("1566712", {"width":202,"hash":"152d981622fe31781498da5b1e42963abafda46f7942760baa2e35b06b309976","haswebp":1,"name":"6.jpg","height":300,"hasavif":0}, "webpsmalltn", "webp","tn") -> "//btn.hitomi.la/webpsmalltn/6/97/152d981622fe31781498da5b1e42963abafda46f7942760baa2e35b06b309976.webp" common.js:70:8
  url_from_url_from_hash("1566712", {"width":202,"hash":"152d981622fe31781498da5b1e42963abafda46f7942760baa2e35b06b309976","haswebp":1,"name":"6.jpg","height":300,"hasavif":0}, "smalltn", "jpg","tn") -> "//btn.hitomi.la/smalltn/6/97/152d981622fe31781498da5b1e42963abafda46f7942760baa2e35b06b309976.jpg" common.js:70:8
  url_from_url_from_hash("1566712", {"width":202,"hash":"ba00573b20260b0ad87578d59ad273ec15f9e70dc13ac579066665b89e49f011","haswebp":1,"name":"7.jpg","height":300,"hasavif":0}, "webpsmallsmalltn", "webp","tn") -> "//btn.hitomi.la/webpsmallsmalltn/1/01/ba00573b20260b0ad87578d59ad273ec15f9e70dc13ac579066665b89e49f011.webp" common.js:70:8
  url_from_url_from_hash("1566712", {"width":202,"hash":"ba00573b20260b0ad87578d59ad273ec15f9e70dc13ac579066665b89e49f011","haswebp":1,"name":"7.jpg","height":300,"hasavif":0}, "webpsmalltn", "webp","tn") -> "//btn.hitomi.la/webpsmalltn/1/01/ba00573b20260b0ad87578d59ad273ec15f9e70dc13ac579066665b89e49f011.webp" common.js:70:8
  url_from_url_from_hash("1566712", {"width":202,"hash":"ba00573b20260b0ad87578d59ad273ec15f9e70dc13ac579066665b89e49f011","haswebp":1,"name":"7.jpg","height":300,"hasavif":0}, "smalltn", "jpg","tn") -> "//btn.hitomi.la/smalltn/1/01/ba00573b20260b0ad87578d59ad273ec15f9e70dc13ac579066665b89e49f011.jpg" common.js:70:8
  url_from_url_from_hash("1566712", {"width":202,"hash":"c695e220937ea67f3ab73d947c1b3d6ddfd45f3009ef9f0ee59dbf40b457c745","haswebp":1,"name":"8.jpg","height":300,"hasavif":0}, "webpsmallsmalltn", "webp","tn") -> "//ctn.hitomi.la/webpsmallsmalltn/5/74/c695e220937ea67f3ab73d947c1b3d6ddfd45f3009ef9f0ee59dbf40b457c745.webp" common.js:70:8
  url_from_url_from_hash("1566712", {"width":202,"hash":"c695e220937ea67f3ab73d947c1b3d6ddfd45f3009ef9f0ee59dbf40b457c745","haswebp":1,"name":"8.jpg","height":300,"hasavif":0}, "webpsmalltn", "webp","tn") -> "//ctn.hitomi.la/webpsmalltn/5/74/c695e220937ea67f3ab73d947c1b3d6ddfd45f3009ef9f0ee59dbf40b457c745.webp" common.js:70:8
  url_from_url_from_hash("1566712", {"width":202,"hash":"c695e220937ea67f3ab73d947c1b3d6ddfd45f3009ef9f0ee59dbf40b457c745","haswebp":1,"name":"8.jpg","height":300,"hasavif":0}, "smalltn", "jpg","tn") -> "//ctn.hitomi.la/smalltn/5/74/c695e220937ea67f3ab73d947c1b3d6ddfd45f3009ef9f0ee59dbf40b457c745.jpg" common.js:70:8
  
'''