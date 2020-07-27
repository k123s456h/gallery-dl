# -*- coding: utf-8 -*-
#########################################################
# python
import os
import traceback
import json
from datetime import datetime

# third-party

# sjva 공용
from framework import app, path_app_root, db

# 패키지
from .plugin import package_name, logger

db_file = os.path.join(path_app_root, 'data', 'db', '%s.db' % package_name)
app.config['SQLALCHEMY_BINDS'][package_name] = 'sqlite:///%s' % (db_file)


class ModelSetting(db.Model):
    __tablename__ = '%s_setting' % package_name
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = package_name

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String, nullable=False)

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return repr(self.as_dict())

    def as_dict(self):
        return {x.name: getattr(self, x.name) for x in self.__table__.columns}

    @staticmethod
    def get(key):
        try:
            return db.session.query(ModelSetting).filter_by(key=key).first().value.strip()
        except Exception as e:
            logger.error('Exception:%s %s', e, key)
            logger.error(traceback.format_exc())
            
    
    @staticmethod
    def get_int(key):
        try:
            return int(ModelSetting.get(key))
        except Exception as e:
            logger.error('Exception:%s %s', e, key)
            logger.error(traceback.format_exc())
    
    @staticmethod
    def get_bool(key):
        try:
            return (ModelSetting.get(key) == 'True')
        except Exception as e:
            logger.error('Exception:%s %s', e, key)
            logger.error(traceback.format_exc())

    @staticmethod
    def set(key, value):
        try:
            item = db.session.query(ModelSetting).filter_by(key=key).with_for_update().first()
            if item is not None:
                item.value = value.strip()
                db.session.commit()
            else:
                db.session.add(ModelSetting(key, value.strip()))
        except Exception as e:
            logger.error('Exception:%s %s', e, key)
            logger.error(traceback.format_exc())

    @staticmethod
    def to_dict():
        try:
            from framework.util import Util
            return Util.db_list_to_dict(db.session.query(ModelSetting).all())
        except Exception as e:
            logger.error('Exception:%s %s', e, key)
            logger.error(traceback.format_exc())


    @staticmethod
    def setting_save(req):
        try:
            for key, value in req.form.items():
                if key in ['scheduler', 'is_running']:
                    continue
                
                if key == "gallery-dl_option_value":
                    ### json grammar check
                    value = value.replace(u"'", u'"')
                    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gallery-dl.conf'), 'w') as gdl_conf:
                        gdl_conf.write(value)
                        gdl_conf.close()
                else:
                    logger.debug('Key:%s Value:%s', key, value)
                    entity = db.session.query(ModelSetting).filter_by(key=key).with_for_update().first()
                    entity.value = value
                
            db.session.commit()
            return True                  
        except Exception as e: 
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            logger.debug('Error Key:%s Value:%s', key, value)
            return False

#########################################################


class ModelGalleryDlItem(db.Model):
    # id  json  created_time  title  artist  series  category  url  total_image_count index status
    # int json  datetime      str    str     str     str  int

    __tablename__ = 'plugin_%s_item' % package_name
    __table_args__ = {'mysql_collate': 'utf8_general_ci'}
    __bind_key__ = package_name

    id = db.Column(db.Integer, primary_key=True)
    json = db.Column(db.JSON)
    created_time = db.Column(db.DateTime)

    title = db.Column(db.String)
    artist = db.Column(db.String)
    parody = db.Column(db.String)
    category = db.Column(db.String)
    url = db.Column(db.String)
    total_image_count = db.Column(db.Integer)
    status = db.Column(db.String)

    def __init__(self):
        self.created_time = datetime.now()
        self.title = ''
        self.artist = ''
        self.parody = ''
        self.category = ''
        self.url = ''
        self.total_image_count = 0
        self.status = ''

    def as_dict(self):
        ret = {x.name: getattr(self, x.name) for x in self.__table__.columns}
        ret['created_time'] = self.created_time.strftime('%Y-%m-%d %H:%M:%S') 
        return ret
    
    # @staticmethod
    # def save(entity):
    #     m = ModelGalleryDlItem()
    #     m.title = entity.title
    #     m.artist = entity.artist
    #     m.parody = entity.parody
    #     m.category = entity.category
    #     m.total_image_count = entity['total_image_count']
    #     m.url = entity['url']
    #     m.status = entity['status']
    #     db.session.add(m)
    #     db.session.commit()

    @staticmethod
    def save_as_dict(d):
        try:
            logger.debug(d)
            entity = db.session.query(ModelGalleryDlItem).filter_by(id=d['id']).with_for_update().first()
            if entity is not None:
                entity.status = unicode(d['status'])
                entity.title = unicode(d['title'])
                entity.artist = unicode(d['artist'])
                entity.parody = unicode(d['parody'])
                entity.category = unicode(d['category'])
                entity.total_image_count = d['total_image_count']
                entity.url = unicode(d['url'])

                db.session.commit()
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())

    @staticmethod
    def get(url):
        try:
            entity = db.session.query(ModelGalleryDlItem).filter_by(url=url).first()
            if entity is not None:
                return entity.as_dict()
            else:
                return None
        except Exception as e:
            logger.error('Exception:%s %s', e, url)
            logger.error(traceback.format_exc())

    @staticmethod
    def init(url):
        try:
            entity = db.session.query(ModelGalleryDlItem).filter_by(url=url).first()
            if entity is None:
                entity = ModelGalleryDlItem()
                entity.url = url
                entity.created_time = datetime.now()
                entity.status = u'대기'
                db.session.add(entity)
                db.session.commit()
            # else:
            #     if entity.status == '완료':
            #         return None
            return entity.as_dict()
        except Exception as e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
    
    @staticmethod
    def delete(id):
        try:
            item = db.session.query(ModelGalleryDlItem).filter_by(id=id).first()
            if item is not None:
                db.session.delete(item)
                db.session.commit()
            return True
        except Exception, e:
            logger.error('Exception:%s', e)
            logger.error(traceback.format_exc())
            return False