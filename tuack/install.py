# -*- coding: utf-8 -*-

from __future__ import print_function
import os
import re
import sys
import json
import datetime
import shutil
import subprocess
import time
import signal
import zipfile
from multiprocessing import Process, Queue
from functools import wraps
from threading import Timer
import platform
from . import base
from .base import log, pjoin, rjoin
import traceback
import __main__

def format():
	fname = base.format_checker_name
	if base.system != 'Windows':
		install_path = '/'.join(__main__.__file__.split('/')[:-1]) + '/lex'
	else:
		install_path = __main__.__file__ + '\\..\\lex'
	shutil.copy(pjoin(install_path, fname), base.tool_path)
	fpath = pjoin(base.tool_path, fname)
	if base.system != 'Windows':
		os.system('chmod +x %s' % fpath)
		ret = os.system('%s -v' % fpath)
	else:
		ret = os.system('%s -v' % fpath)
	if ret == 0:
		log.info(u'`format`安装成功。')
		return
	log.info(u'直接安装format checker失败，请尝试用以下方式手工编译：')
	log.info(u'1. 先安装flex和bison两个工具。')
	log.info(u'2. 在目录tuack/lex下运行`python compile.pyinc`或在其他地方运行后将编译好的文件复制进该目录。')
	log.info(u'3. 重新运行`python -m tuack.install format`。')

def pre_check(name):
	def runner():
		log.info(u'尝试安装`%s`。' % name)
		'''
		try:
			base.check_install(name)
			log.info(u'`%s`已安装，跳过安装。' % name)
			return
		except Exception as e:
		'''
		eval(name)()
	return runner

packages = ['format']
work_list = {key : pre_check(key) for key in packages}
work_list['full'] = lambda : [work_list[key]() for key in work_list if key not in {'full', 'std'}]
work_list['std'] = lambda : [work_list[key]() for key in ('format',)]

if __name__ == '__main__':
	try:
		result = base.init()
	except base.NoFileException as e:
		base.conf = None
		result = True
	if result:
		for base.work in base.works:
			base.run_exc(work_list[base.work])
	else:
		log.info(u'这个工具用于引导安装tuack的组件。')
		log.info(u'支持的工作：')
		log.info(u'  std      标准安装，包含常用小型工具。')
		log.info(u'  full     完整安装，包含所有工具，可能会很大。')
		log.info(u'  format   题面格式检查器。')
