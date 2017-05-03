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
import common
from common import log

def tsinsen_oj():
	new_tc = []
	
	class Base(object):
		def __init__(self):
			pass
		def write(self, text):
			pass
		def close(self):
			pass
	class Conf(Base):
		def __init__(self, *names):
			self.names = names
			self.buff = b''
		def write(self, text):
			self.buff += text
		def close(self):
			cur = self.buff.decode('utf-8').strip()
			for name in reversed(self.names[1:]):
				if not name:
					cur = [cur]
				else:
					cur = {name : cur}
			common.conf[self.names[0]] = cur
	class File(Base):
		def __init__(self, *names):
			path = ''
			for name in names[:-1]:
				path = common.pjoin(path, name)
				if not os.path.exists(path):
					os.makedirs(path)
			self.f = open(common.pjoin(*names), 'wb')
		def write(self, text):
			self.f.write(text)
		def close(self):
			self.f.close()
	class HtmlFile(Base):
		def __init__(self, *names):
			path = ''
			for name in names[:-1]:
				path = common.pjoin(path, name)
				if not os.path.exists(path):
					os.makedirs(path)
			self.fname = common.pjoin(*names)
			self.buff = b''
		def write(self, text):
			self.buff += text
		def close(self):
			ret = json.dumps(json.dumps(self.buff.decode('utf-8'))).encode('utf-8')
			f = open(self.fname, 'wb')
			f.write(b'{{ self.title() }}\n')
			f.write(b'{{ render(%s, \'html\') }}\n' % ret)
			f.close()
	Title = lambda : Conf('title', 'zh-cn')
	CheckPoint = lambda : Conf('key words')
	Checkers = Base
	TestMethod = Base
	InputFileName = Base
	OutputFileName = Base
	Description = lambda : HtmlFile('statement', 'zh-cn.md')
	Judger = lambda : File('data', 'chk', 'chk.cpp')
	
	class TimeLimit(Conf):
		def __init__(self):
			super(TimeLimit, self).__init__('time limit')
		def close(self):
			self.buff = self.buff.strip()[:-1]
			super(TimeLimit, self).close()
	
	class MemoryLimit(Conf):
		def __init__(self):
			super(MemoryLimit, self).__init__('memory limit')
		def close(self):
			if len(self.buff) >= 2:
				s = self.buff.strip().decode('utf-8')
				sp = 1 if '0' <= s[-2] <= '9' else 2
				self.buff = (s[:-sp] + ' ' + s[-sp:]).encode('utf-8')
			super(MemoryLimit, self).close()
	
	class Solution(File):
		def __init__(self):
			super(Solution, self).__init__('tsinsen-oj', 'std', 'std.cpp')
		def close(self):
			super(Solution, self).close()
			if 'users' not in common.conf:
				common.conf['users'] = {}
			if 'tsinsen-oj' not in common.conf['users']:
				common.conf['users']['tsinsen-oj'] = {}
			common.conf['users']['tsinsen-oj']['std'] = 'tsinsen-oj/std/std.cpp'
			
	class InData(File):
		last_in = None
		def __init__(self):
			tc = set(common.conf.test_cases)
			for i in range(1, len(tc) + 2):
				if str(i) not in tc:
					name = i
			new_tc.append(name)
			common.conf.test_cases.append(name)
			InData.last_in = name
			super(InData, self).__init__('data', '%d.in' % name)
			
	class OutData(File):
		def __init__(self):
			super(OutData, self).__init__('data', '%d.out' % InData.last_in)

	if common.conf.folder != 'problem':
		log.error(u'只能导入到一个problem的工程中。')
		return
	status = None
	for line in open(common.args[0], 'rb'):
		if not status:			# 啥都没有
			try:
				buffer = eval(line.decode('utf-8').strip()[:-1])()
			except Exception as e:
				log.warning(str(e))
				buffer = Base()
			status = True
		elif status == True:	# 读到了等号的行，还没读到标记开始的行
			status = line
		elif status == line:	# 读到了标记结束的行
			buffer.close()
			status = None
		else:					# 读到了标记开始的行，还没读到标记结束的行
			buffer.write(line)
	if len(new_tc) > 0:
		if 'data' not in common.conf:
			common.conf['data'] = []
		common.conf['data'].append({'cases' : new_tc})
	common.save_json(common.conf)

work_list = {
	'tsinsen-oj' : tsinsen_oj
}

if __name__ == '__main__':
	try:
		if common.init() and len(common.args) != 0:
			for common.work in common.works:
				common.run_exc(work_list[common.work])
		else:
			log.info(u'这个工具用于导入其他类型的工程，参数1必须是来源路径。')
			log.info(u'支持的工作：%s' % ','.join(work_list.keys()))
	except common.NoFileException as e:
		log.error(e)
		log.info(u'尝试使用`python -m generator -h`获取如何生成一个工程。')
