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
from .base import log

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
			if type(self.buff) == bytes:
				cur = self.buff.decode('utf-8').strip()
			else:
				cur = self.buff
			for name in reversed(self.names[1:]):
				if not name:
					cur = [cur]
				else:
					cur = {name : cur}
			base.conf[self.names[0]] = cur
	class File(Base):
		def __init__(self, *names):
			path = ''
			for name in names[:-1]:
				path = base.pjoin(path, name)
				if not os.path.exists(path):
					os.makedirs(path)
			self.f = open(base.pjoin(*names), 'wb')
		def write(self, text):
			self.f.write(text)
		def close(self):
			self.f.close()
	class HtmlFile(Base):
		def __init__(self, *names):
			path = ''
			for name in names[:-1]:
				path = base.pjoin(path, name)
				if not os.path.exists(path):
					os.makedirs(path)
			self.fname = base.pjoin(*names)
			self.buff = b''
		def write(self, text):
			self.buff += text.strip() + b'\n'
		def close(self):
			ret = json.dumps(json.dumps(self.buff.decode('utf-8'))).encode('utf-8')
			f = open(self.fname, 'wb')
			f.write(b'{{ self.title() }}\n')
			f.write(b'{{ render(%s, \'html\') }}\n' % ret)
			f.close()
	class FileName(Base):
		last_name = None
		def write(self, text):
			FileName.last_name = text.decode('utf-8').rstrip('\n\r')
	class Base64File(Base):
		def __init__(self):
			self.buff = b''
		def write(self, text):
			self.buff += text
		def close(self):
			import base64
			if not os.path.exists('resources'):
				os.makedirs('resources')
			open(base.pjoin('resources', FileName.last_name), 'wb').write(base64.b64decode(self.buff))
	Title = lambda : Conf('title', 'zh-cn')
	CheckPoint = lambda : Conf('key words')
	TestMethod = Base
	InputFileName = Base
	OutputFileName = Base
	Description = lambda : HtmlFile('statement', 'zh-cn.md')
	Judger = lambda : File('data', 'chk', 'chk.cpp')
	
	class TimeLimit(Conf):
		def __init__(self):
			super(TimeLimit, self).__init__('time limit')
		def close(self):
			self.buff = float(self.buff.strip()[:-1])
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
			if 'users' not in base.conf:
				base.conf['users'] = {}
			if 'tsinsen-oj' not in base.conf['users']:
				base.conf['users']['tsinsen-oj'] = {}
			base.conf['users']['tsinsen-oj']['std'] = 'tsinsen-oj/std/std.cpp'
			
	class InData(File):
		last_in = None
		def __init__(self):
			tc = set(base.conf.test_cases)
			for i in range(1, len(tc) + 2):
				if str(i) not in tc:
					name = i
			new_tc.append(name)
			base.conf.test_cases.append(name)
			InData.last_in = name
			super(InData, self).__init__('data', '%d.in' % name)
			
	class OutData(File):
		def __init__(self):
			super(OutData, self).__init__('data', '%d.ans' % InData.last_in)
			
	class Checkers(File):
		fname = ('data', 'chk', 'chk.cpp')
		def __init__(self):
			super(Checkers, self).__init__(*Checkers.fname)
		def close(self):
			super(Checkers, self).close()
			if os.path.getsize(base.pjoin(*Checkers.fname)) < 10:
				shutil.rmtree(base.pjoin(*Checkers.fname[:2]), ignore_errors = True)
	import re
	key_re = re.compile('(\w*)\((\w*)\)')

	if base.conf.folder != 'problem':
		log.error(u'只能导入到一个problem的工程中。')
		return
	status = None
	for line in open(base.args[0], 'rb'):
		if not status:			# 啥都没有
			try:
				key = line.decode('utf-8').strip()[:-1]
				m = key_re.match(key)
				if m:
					if m.group(1) == 'File':
						log.warning(u'题面含有文件，请在题面中手工查找字符串`%s`并进行相应修改，该文件保存在`resources/%s`。' % (
							m.group(2), FileName.last_name
						))
						buffer = Base64File()
					else:
						log.warning(u'无法解析关键词`%s`。' % key)
				else:
					buffer = eval(key)()
			except Exception as e:
				log.warning(u'无法解析关键词`%s`。' % key)
				log.debug(e)
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
		if 'data' not in base.conf:
			base.conf['data'] = []
		base.conf['data'].append({'cases' : new_tc})
	base.save_json(base.conf)

work_list = {
	'tsinsen-oj' : tsinsen_oj
}

if __name__ == '__main__':
	try:
		if base.init() and len(base.args) != 0:
			for base.work in base.works:
				base.run_exc(work_list[base.work])
		else:
			log.info(u'这个工具用于导入其他类型的工程，参数1必须是来源路径。')
			log.info(u'支持的工作：%s' % ','.join(sorted(work_list.keys())))
	except base.NoFileException as e:
		log.error(e)
		log.info(u'尝试使用`python -m tuack.gen -h`获取如何生成一个工程。')
