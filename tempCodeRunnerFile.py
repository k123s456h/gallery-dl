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


def reqtext(url):
    import requests
    import json
    t = requests.get(url).text[18:]
    j = json.loads(t)
    return j

m = reqtext('https://ltn.hitomi.la/galleries/1692965.js')
print(m['files'][0])