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
from .base import log, pjoin

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

def syzoj(style = 'loj', cookies = None):
	if base.conf.folder != 'problem':
		log.error(u'只能导入到一个problem的工程中。')
		return
	import requests
	try:
		headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
		r = requests.get(base.args[0] + '/export', headers = headers, cookies = cookies)
		data = json.loads(r.content)
		assert(data['success'])
		data = data['obj']
	except Exception as e:
		log.error(u'下载或解析`' + base.args[0] + '/export`失败。')
		log.info(e)
	conf = base.conf
	conf['time limit'] = float(data.get('time_limit', 1000)) / 1000.
	conf['memory limit'] = str(data.get('memory_limit', 512)) + ' MiB'
	conf['type'] = {'traditional' : 'program', 'submit-answer' : 'output'}.get(data.get('type'), 'interactive')
	conf['key words'] = data.get('tags', [])
	conf.setdefault('title', {})
	conf['title']['zh-cn'] = data.get('title', u'标题读取失败')
	with open('statement/zh-cn.md', 'wb') as f:
		f.write(b'{{ self.title() }}\n\n')
		if style != 'ipuoj':
			for key, name in [
				('description', u'题目描述'),
				('input_format', u'输入格式'),
				('output_format', u'输出格式'),
				('example', u'样例'),
				('limit_and_hint', u'子任务')
			]:
				if key in data:
					f.write(('## %s\n\n' % name).encode('utf-8'))
					f.write(data[key].encode('utf-8'))
					f.write(b'\n\n')
		else:
			f.write(data['description'].encode('utf-8'))
			f.write(b'\n\n')
	def download_file(url, local_filename):
		with requests.get(url, headers = headers, stream = True, cookies = cookies) as r:
			r.raise_for_status()
			with open(local_filename, 'wb') as f:
				for chunk in r.iter_content(chunk_size = 8192): 
					if chunk:
						f.write(chunk)
						f.flush()
	import zipfile
	download_file(base.args[0] + '/testdata/download', 'data.zip')
	with zipfile.ZipFile('data.zip', 'r') as z:
		z.extractall('data')
		for name in os.listdir('data'):
			if name.endswith('.out'):
				if os.path.exists(pjoin('data', name[:-4] + '.ans')):
					os.remove(pjoin('data', name[:-4] + '.ans'))
					time.sleep(.1)
				os.rename(pjoin('data', name), pjoin('data', name[:-4] + '.ans'))
	if data.get('have_additional_file'):
		download_file(base.args[0] + '/download/additional_file', 'down.zip')
		with zipfile.ZipFile('down.zip', 'r') as z:
			z.extractall('down')
	else:
		shutil.rmtree('down')
		time.sleep(.1)
		os.makedirs('down')
	shutil.rmtree('pre')
	time.sleep(.1)
	os.makedirs('pre')
	base.save_json(base.conf)
	from . import gen
	base.run_exc(gen.work_list['auto'])

def ipuoj():
	tool_conf = base.tool_conf['ipuoj']['default']
	cookies = tool_conf['cookies']
	syzoj('ipuoj', cookies)

def loj():
	syzoj('loj')

def data_folder(bpath = None):
	if base.conf.folder != 'problem':
		log.error(u'只能导入到一个problem的工程中。')
		return
	if bpath is None:
		bpath = base.args[0]
	cases = set(base.conf.test_cases)
	idx = [1]	# python2居然不支持nonlocal，只能用这种鬼畜方法实现闭包了
	while idx[0] in cases or str(idx[0]) in cases:
		idx[0] += 1
	def save(path, iname, oname):
		log.info(u'找到数据`%s/{%s,%s}`' % (path, iname, oname))
		shutil.copyfile(pjoin(path, iname), pjoin(base.conf.path, 'data', str(idx[0]) + '.in'))
		shutil.copyfile(pjoin(path, oname), pjoin(base.conf.path, 'data', str(idx[0]) + '.ans'))
		idx[0] += 1
	re_inp = re.compile('(.*)input(.*)')
	re_in = re.compile('(.*)\\.in(.*)')
	def scan(path):
		for fname in os.listdir(path):
			flag = False
			fpath = pjoin(path, fname)
			if os.path.isfile(fpath):
				for re_i, ostrs in ((re_inp, ('answer', 'output')), (re_in, ('.ans', '.out'))):
					ma = re_i.match(fname)
					if ma:
						for ostr in ostrs:
							oname = ma.group(1) + ostr + ma.group(2)
							if os.path.exists(pjoin(path, oname)):
								save(path, fname, oname)
								flag = True
								break
						if flag:
							break
			else:
				scan(fpath)
	scan(bpath)
	from . import gen
	base.run_exc(gen.work_list['data'])

def data_pack(suf, bpath = None):
	import zipfile, tarfile, rarfile
	packer = {
		'zip' : zipfile.ZipFile,
		'rar' : rarfile.RarFile,
		'tar' : tarfile.TarFile
	}.get(suf, None)
	if suf == 'rar':
		base.check_install('unrar')
	if not packer:
		log.error(u'暂时不支持的压缩包类型。')
		return
	if base.conf.folder != 'problem':
		log.error(u'只能导入到一个problem的工程中。')
		return
	if bpath is None:
		bpath = base.args[0]
	with packer(bpath) as z:
		z.extractall('tmp')
	data_folder('tmp')
	time.sleep(.1)
	shutil.rmtree('tmp')

def data(bpath = None):
	if base.conf.folder != 'problem':
		log.error(u'只能导入到一个problem的工程中。')
		return
	if bpath is None:
		bpath = base.args[0]
	suffix = [
		('.rar', 'rar'),
		('.zip', 'zip'),
		('.tar.gz', 'tar'),
		('.tar', 'tar')
	]
	if os.path.isfile(bpath):
		for suf, tp in suffix:
			if bpath.endswith(suf):
				data_pack(tp, bpath)
				break
		else:
			log.error(u'暂时不支持的压缩包类型。')
	else:
		data_folder(bpath)

work_list = {
	'tsinsen-oj' : tsinsen_oj,
	'loj' : loj,
	'ipuoj' : ipuoj,
	'data' : data,
	'data-folder' : data_folder,
	'data-zip' : lambda : data_pack('zip'),
	'data-tar' : lambda : data_pack('tar'),
	'data-rar' : lambda : data_pack('rar')
}

if __name__ == '__main__':
	try:
		if base.init() and len(base.args) != 0:
			for base.work in base.works:
				base.run_exc(work_list[base.work])
		else:
			log.info(u'这个工具用于导入其他类型的工程，参数1必须是来源路径。')
			#log.info(u'支持的工作：%s' % ','.join(sorted(work_list.keys())))
			log.info(u'支持的工作：')
			log.info(u'  tsinsen-oj  参数1是符合清澄OJ“我来出题”的上传下载格式的本地文件。')
			log.info(u'  loj         参数1是SYZ系OJ的题目网站如“https://loj.ac/problem/1”。')
			log.info(u'  data        参数1是一个装数据的文件夹或压缩包，只导入数据。')
			log.info(u'  data-folder 在上述命令不好使的时候，强制指定是文件夹。')
			log.info(u'  data-zip    在上述命令不好使的时候，强制指定是zip文件。')
			log.info(u'  data-tar    在上述命令不好使的时候，强制指定是tar文件。')
			log.info(u'  data-rar    在上述命令不好使的时候，强制指定是rar文件。')
	except base.NoFileException as e:
		log.error(e)
		log.info(u'尝试使用`python -m tuack.gen -h`获取如何生成一个工程。')
