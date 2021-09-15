import functools
import os
import sys
import time
import zipfile
from logging import FileHandler, Formatter, Logger, DEBUG, StreamHandler, INFO
from threading import RLock

from colorlog import ColoredFormatter

LOGGING_DIR = os.path.join('logs')
DEBUG_SWITCH = False


class SyncStdoutStreamHandler(StreamHandler):
	__write_lock = RLock()

	def __init__(self):
		super().__init__(sys.stdout)

	def emit(self, record) -> None:
		with self.__write_lock:
			super().emit(record)


def _create_file_handler(name: str) -> FileHandler:
	logging_file_path: str = os.path.join(LOGGING_DIR, 'chatbridge_{}.log'.format(name))
	if not os.path.isdir(os.path.dirname(logging_file_path)):
		os.makedirs(os.path.dirname(logging_file_path))

	if os.path.isfile(logging_file_path):
		modify_time = '{}_{}'.format(time.strftime('%Y-%m-%d', time.localtime(os.stat(logging_file_path).st_mtime)), name)
		counter = 0
		while True:
			counter += 1
			zip_file_name = '{}/{}-{}.zip'.format(os.path.dirname(logging_file_path), modify_time, counter)
			if not os.path.isfile(zip_file_name):
				break
		zipf = zipfile.ZipFile(zip_file_name, 'w')
		zipf.write(logging_file_path, arcname=os.path.basename(logging_file_path), compress_type=zipfile.ZIP_DEFLATED)
		zipf.close()
		os.remove(logging_file_path)
	file_handler = FileHandler(logging_file_path, encoding='utf8')
	file_handler.setFormatter(Formatter(
		'[%(name)s] [%(asctime)s] [%(threadName)s/%(levelname)s]: %(message)s',
		datefmt='%Y-%m-%d %H:%M:%S'
	))
	return file_handler


class ChatBridgeLogger(Logger):
	LOG_COLORS = {
		'DEBUG': 'blue',
		'INFO': 'green',
		'WARNING': 'yellow',
		'ERROR': 'red',
		'CRITICAL': 'bold_red',
	}
	SECONDARY_LOG_COLORS = {
		'message': {
			'WARNING': 'yellow',
			'ERROR': 'red',
			'CRITICAL': 'red'
		}
	}

	def __init__(self, name: str):
		super().__init__(name)
		self.console_handler = SyncStdoutStreamHandler()
		self.console_handler.setFormatter(ColoredFormatter(
			f'[%(name)s] [%(asctime)s] [%(threadName)s/%(log_color)s%(levelname)s%(reset)s]: %(message_log_color)s%(message)s%(reset)s',
			log_colors=self.LOG_COLORS,
			secondary_log_colors=self.SECONDARY_LOG_COLORS,
			datefmt='%H:%M:%S'
		))
		self.file_handler = _create_file_handler(self.name)
		self.addHandler(self.console_handler)
		self.addHandler(self.file_handler)
		self.setLevel(DEBUG if DEBUG_SWITCH else INFO)
