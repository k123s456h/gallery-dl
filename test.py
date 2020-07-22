import os
import json
import requests
import urllib
from fake_useragent import UserAgent

class LogicHitomi:
  headers = {
                'User-Agent': UserAgent(cache=False).random,
                'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language' : 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
            } 

  basepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hitomi-data')
  if not os.path.isdir(basepath):
    os.mkdir(basepath)

  baseurl = 'https://hitomi.la/galleries/'
  #json_list = []
  json_list = ['galleries0.json', 'galleries1.json', 'galleries2.json', 'galleries3.json', 
  'galleries4.json', 'galleries5.json', 'galleries6.json', 'galleries7.json', 
  'galleries8.json', 'galleries9.json', 'galleries10.json', 'galleries11.json', 
  'galleries12.json', 'galleries13.json', 'galleries14.json', 'galleries15.json', 
  'galleries16.json', 'galleries17.json', 'galleries18.json', 'galleries19.json'] # dev

  @staticmethod
  def get_response(url):
    try:
      return requests.get(url,headers=LogicHitomi.headers).text.decode('utf-8')
    except Exception as e:
      pass
  
  @staticmethod
  def bundlejson():
    try:
      bundlejsonurl = 'https://kurtbestor.pythonanywhere.com/h_data'
      res = LogicHitomi.get_response(bundlejsonurl)
      bundle_json = json.loads(res) 
      return bundle_json
    except Exception as e:
      print(e)
      pass

  @staticmethod
  def download_json():
    try:
      bundle_json = LogicHitomi.bundlejson()
      for [name, url] in bundle_json["urls"]:
        urllib.urlretrieve(url, os.path.join(LogicHitomi.basepath, name))
        LogicHitomi.json_list.append(name)
      pass
    except Exception as e:
      print(e)
      pass

  @staticmethod
  def process_json(condition):
    # condition: { key1:val1, key2:val2 }
    # key:
    # a, l, n, t, type, i, p, g, c
    # galleries0.json is the latest
    ret = []
    if len(condition) == 0:
      return ret

    for item in LogicHitomi.json_list:
      with open(os.path.join(LogicHitomi.basepath, item)) as galleries:
        json_item = json.loads(galleries.read())

        for idx, gallery in enumerate(json_item):
          try:
            print(idx, gallery)
            break
          except Exception as e:
            import traceback
            print('Exception:%s', e)
            print(traceback.format_exc())
            # no such key for this item
            pass
        
        galleries.close()
    
    return ret


import time
start = time.time()

#LogicHitomi.download_json()
#print("download time :", time.time() - start)
print(LogicHitomi.process_json({"a":"seto yuuki"}))

print("process+download time :", time.time() - start)