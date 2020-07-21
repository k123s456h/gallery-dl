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
    # id  json  created_time  title  artist  series  url  total_image_count
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
    status = db.Column(db.Integer)

    def __init__(self, url):
        self.created_time = datetime.now()
        self.url = url
        self.status = u"대기"


    def as_dict(self):
        ret = {x.name: getattr(self, x.name) for x in self.__table__.columns}
        ret['created_time'] = self.created_time.strftime('%m-%d %H:%M:%S') 
        return ret
    
    @staticmethod
    def save(entity):
        m = ModelGalleryDlItem()
        m.title = entity.title
        m.artist = entity.artist
        m.parody = entity.parody
        m.category = entity.category
        m.total_image_count = entity.total_image_count
        m.url = entity.url
        db.session.add(m)
        db.session.commit()

    @staticmethod
    def get(url):
        try:
            return db.session.query(ModelGalleryDlItem).filter_by(url=url).first()
        except Exception as e:
            logger.error('Exception:%s %s', e, url)
            logger.error(traceback.format_exc())
