# -*- coding: utf-8 -*-
#########################################################
# python
import traceback
from datetime import datetime

# third-party
from flask import jsonify

# 패키지
from .plugin import logger
from .logic_gallerydl import LogicGalleryDL
#########################################################

class LogicNormal(object):
	gallery_dl_list = []

	@staticmethod
	def get_data(youtube_dl):
		try:
			data = {}
			data['plugin'] = youtube_dl.plugin
			data['url'] = youtube_dl.url
			data['filename'] = youtube_dl.filename
			data['temp_path'] = youtube_dl.temp_path
			data['save_path'] = youtube_dl.save_path
			data['index'] = youtube_dl.index
			data['status_str'] = youtube_dl.status.name
			data['status_ko'] = str(youtube_dl.status)
			data['end_time'] = ''
			data['extractor'] = youtube_dl.info_dict['extractor'] if youtube_dl.info_dict['extractor'] is not None else ''
			data['title'] = youtube_dl.info_dict['title'] if youtube_dl.info_dict['title'] is not None else youtube_dl.url
			data['uploader'] = youtube_dl.info_dict['uploader'] if youtube_dl.info_dict['uploader'] is not None else ''
			data['uploader_url'] = youtube_dl.info_dict['uploader_url'] if youtube_dl.info_dict['uploader_url'] is not None else ''
			data['downloaded_bytes_str'] = ''
			data['total_bytes_str'] = ''
			data['percent'] = '0'
			data['eta'] = youtube_dl.progress_hooks['eta'] if youtube_dl.progress_hooks['eta'] is not None else ''
			data['speed_str'] = LogicNormal.human_readable_size(youtube_dl.progress_hooks['speed'], '/s') if youtube_dl.progress_hooks['speed'] is not None else ''
			if youtube_dl.status == Status.READY:	# 다운로드 전
				data['start_time'] = ''
				data['download_time'] = ''
			else:
				if youtube_dl.end_time is None:	# 완료 전
					download_time = datetime.now() - youtube_dl.start_time
				else:
					download_time = youtube_dl.end_time - youtube_dl.start_time
					data['end_time'] = youtube_dl.end_time.strftime('%m-%d %H:%M:%S')
				if None not in (youtube_dl.progress_hooks['downloaded_bytes'], youtube_dl.progress_hooks['total_bytes']):	# 둘 다 값이 있으면
					data['downloaded_bytes_str'] = LogicNormal.human_readable_size(youtube_dl.progress_hooks['downloaded_bytes'])
					data['total_bytes_str'] = LogicNormal.human_readable_size(youtube_dl.progress_hooks['total_bytes'])
					data['percent'] = '%.2f' % (float(youtube_dl.progress_hooks['downloaded_bytes']) / float(youtube_dl.progress_hooks['total_bytes']) * 100)
				data['start_time'] = youtube_dl.start_time.strftime('%m-%d %H:%M:%S')
				data['download_time'] = '%02d:%02d' % (download_time.seconds / 60, download_time.seconds % 60)
			return data
		except Exception as e:
			logger.error('Exception:%s', e)
			logger.error(traceback.format_exc())
			return None

	@staticmethod
	def human_readable_size(size, suffix=''):
		for unit in ('Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB'):
			if size < 1024.0:
				return '%3.1f %s%s' % (size, unit, suffix)
			size /= 1024.0
		return '%.1f %s%s' % (size, 'YB', suffix)

	@staticmethod
	def abort(base, code):
		base['errorCode'] = code
		return jsonify(base)
