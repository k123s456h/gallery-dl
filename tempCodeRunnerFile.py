# from .logic_hitomi import LogicHitomi
import time
start = time.time() 

import os, json
basepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hitomi-data')
last_num = 19


types = ['a', 'g', 't', 'p', 'c', 'l', 'type']
meta = {
  "a": set([]),
  "g": set([]),
  "t": set([]),
  "p": set([]),
  "c": set([]),
  "l": set([]),
  "type": set([])
}
for num in range(0, last_num+1):
  with open(os.path.join(basepath, 'galleries'+str(num)+'.json')) as galleries:
    data = json.loads(galleries.read())
    for gallery in data:
      for key in gallery:
        if key in ['a', 'g', 't', 'p', 'c']:
          for value in gallery[key]:
            if value not in meta[key]:
              meta[key].add(value)
        elif key in ['l', 'type']:
          if gallery[key] not in meta[key]:
            meta[key].add(gallery[key])
    galleries.close()

for _t in meta:
  meta[_t] = list(meta[_t])
  
with open(os.path.join(basepath, 'meta.json'), 'w') as f:
  json.dump(meta, f)
f.close()

print("time :", time.time() - start)
