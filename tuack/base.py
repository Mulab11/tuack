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
import logging
import traceback
import yaml

python_version = sys.version_info.major
if python_version == 2:
	reload(sys)
	sys.setdefaultencoding('utf-8')

class Memory(str):
	'''
	'5KB'，'10 MB'，'8M'格式的字符串s，允许用Memory(s).GB，Memory(s).B等形式转换单位
	'''
	units = {
		'B' : 1,
		'K' : 2 ** 10,
		'KB' : 2 ** 10,
		'M' : 2 ** 20,
		'MB' : 2 ** 20,
		'G' : 2 ** 30,
		'GB' : 2 ** 30,
		'T' : 2 ** 40,
		'TB' : 2 ** 40
	}
	def __new__(self, val):
		return super(Memory, self).__new__(self, val)
	def byte(self):
		if self[-1] == 'B':
			sp = 2 if self[-2] in self.units else 1
		else:
			sp = 1
		un = self.units[self[-sp:]]
		return float(self[:-sp]) * un
	def __init__(self, val):
		super(Memory, self).__init__()
		b = self.byte()
		for key, val in self.units.items():
			self.__setattr__(key, b / val)

json_version = 2
work = None
system = platform.system()
out_system = system
windows_stack_size = 536870912
diff_tool = 'diff' if system != 'Windows' else 'fc'
time_multiplier = 3.
elf_suffix = '' if system != 'Windows' else '.exe'
problem_skip = re.compile(r'^(data|down|tables|resources|gen|pre)$')
user_skip = re.compile(r'^(data|down|pre|val|.*validate.*|gen|chk|checker|report|check.*|make_data|data_maker|data_make|make|dmk|generate|generator|makedata|spj|judge|tables|tmp|.*\.tmp|.*\.temp|temp|.*\.test|.*\.dir)(\..*)?$')
compilers = {
	'cpp' : lambda name, args, macros = '', ml = Memory('512 MB'): 'g++ %s.cpp -o %s %s %s %s' % (name, name, args, macros, '' if system != 'Windows' else '-Wl,--stack=%d' % windows_stack_size),
	'c' : lambda name, args, macros = '', ml = Memory('512 MB'): 'gcc %s.c -o %s %s %s %s' % (name, name, args, macros, '' if system != 'Windows' else '-Wl,--stack=%d' % windows_stack_size),
	# I don't know how to change stack size, nor add #define in pascal
	'pas' : lambda name, args, macros = '', ml = Memory('512 MB'): 'fpc %s.pas %s' % (name, args),
	'java' : lambda name, args, macros = '', ml = Memory('512 MB'): 'javac %s.java %s -J-Xms%dm -J-Xmx%dm' % (name, args, int(Memory(ml).MB) // 16, int(Memory(ml).MB) // 4),
	'py' : lambda name, args, macros = '', ml = Memory('512 MB'): ''
}
runners = {
	'cpp' : None,
	'c' : None,
	'pas' : None,
	'java' : lambda name, ml = None: 'java -Xms%dm -Xmx%dm %s' % (int(Memory(ml).MB) // 16, int(Memory(ml).MB), name),
	'py' : lambda name, ml = None: 'python %s.py' % name
}
macros = {
	'uoj' : '-DONLINE_JUDGE',
	'noi' : '-D__ARBITER__',
	'release' : '',
	'test' : '-D__TUACK__ -DONLINE_JUDGE'
}

copied_data = set()
no_compiling = False
path = os.path.dirname(os.path.realpath(__file__))

log = logging.getLogger()
log.setLevel(logging.DEBUG)

class NoFileException(Exception):
	pass

pjoin = lambda *args : os.path.join(*args).rstrip('/').rstrip('\\')
rjoin = lambda *args : '/'.join(args).strip('/')

natsort_warned = None

tool_path = (path if system == 'Windows' else pjoin(os.path.expanduser("~"), '.tuack'))
if not os.path.exists(tool_path):
	os.makedirs(tool_path)

if system == 'Windows':
	format_checker_name = 'format-win.exe'
elif system == 'Darwin':
	format_checker_name = 'format-mac'
else:
	format_checker_name = 'format-linux'

class Configure(dict):
	'''
	描述一个conf.json的对象
	'''
	@staticmethod
	def merge_item(base, ext):
		'''
		用于合并继承和原始的dict元素
		'''
		if type(base) == type(ext) == list:
			return base + ext
		elif type(base) != dict or type(ext) != dict:
			log.error('Extend conf.json error, type of key `%s` doesn\'t match.' % key)
			raise TypeError('extend error %s' % key)
		ret = base.copy()
		for key, val in ext.items():
			if key.endswith('+'):
				k = key[:-1]
				ret[k] = merge_item(base[k], val)
			else:
				ret[key] = val
		return ret

	def __init__(self, val, path = None, parent = None):
		if type(val) == dict:
			super(Configure, self).__init__(val)
		elif type(val) == str:
			super(Configure, self).__init__(json.loads(val))
		elif type(val) == bytes:
			super(Configure, self).__init__(json.loads(val.decode('utf-8')))
		else:
			raise Exception('Can\'t translate this object to a Configure.')
		self.folder = self['folder']
		self.parent = parent
		self.language = None
		self.path = path
		self.sub = []

	def lang(self):
		return self.language

	def tr(self, key):
		val = self[key]
		if type(val) != dict:
			return val
		if lang and lang in val:
			return val[lang]
		if self.lang() and self.lang() in val:
			return val[self.lang()]
		for k, v in val.items():
			return v
		return None

	def __contains__(self, key):
		return super(Configure, self).__contains__(key + '+') or super(Configure, self).__contains__(key) or (self.parent and key in self.parent)

	def getitem(self, key, trans = lambda prob, val, key, depth : val, depth = 0):
		if super(Configure, self).__contains__(key + '+'):
			cur = trans(self, super(Configure, self).__getitem__(key + '+'), key, depth)
			return self.merge_item(cur, self.parent.getitem(key, trans, depth + 1)) if self.parent else cur
		if super(Configure, self).__contains__(key):
			return trans(self, super(Configure, self).__getitem__(key), key, depth)
		return self.parent.getitem(key, trans, depth + 1) if self.parent else None

	def __getitem__(self, key):
		return self.getitem(key)

	def set_default(self, path = None):
		self.all = True
		if 'name' not in self:
			self['name'] = path
		return self

	def probs(self, pick = False, no_repeat = False):
		if no_repeat == True:
			no_repeat = set()
		if no_repeat != False:
			path = os.path.abspath(self.path)
			if path in no_repeat:
				return
			no_repeat.add(path)
		pick |= not sub_set or self.route in sub_set
		if type(self) == Problem:
			if pick or any_prefix(self.route):
				self.all = pick
				yield self
		else:
			for sub in self.sub:
				for prob in sub.probs(pick, no_repeat = no_repeat):
					yield prob

	def days(self, pick = False, no_repeat = False):
		if no_repeat == True:
			no_repeat = set()
		if no_repeat != False:
			path = os.path.abspath(self.path)
			if path in no_repeat:
				return
			no_repeat.add(path)
		pick |= not sub_set or self.route in sub_set
		if type(self) == Problem:
			return
		if type(self) == Day:
			if pick or any_prefix(self.route):
				self.all = pick
				yield self
		else:
			for sub in self.sub:
				for day in sub.days(pick, no_repeat = no_repeat):
					yield day

	def name_lang(self):
		return self['name'] + ('-' + globals()['lang'] if globals()['lang'] else '')

def probs(item = None, pick = False, no_repeat = False):
	if not item:
		item = conf
	return conf.probs(pick, no_repeat)

def days(item = None, pick = False, no_repeat = False):
	if not item:
		item = conf
	return conf.days(pick, no_repeat)

class Contest(Configure):
	def __init__(self, *args):
		super(Contest, self).__init__(*args)

class Day(Configure):
	def __init__(self, *args):
		super(Day, self).__init__(*args)

class DataPath(str):
	def __new__(self, val):
		return super(DataPath, self).__new__(self, '*' * val['depth'] + val['case'])
	def __init__(self, val):
		self.data = val
		super(DataPath, self).__init__()
	def __getitem__(self, key):
		return self.data[key]
	def full(self):
		return pjoin(self['prefix'], self['key'], self['case'])

def sorter():
	global natsort_warned
	try:
		if not natsort_warned:
			check_install('natsort')
		import natsort
		return lambda inp : natsort.natsorted(inp, alg = natsort.ns.IGNORECASE)
	except:
		if not natsort_warned:
			log.warning(u'`natsort`用于给测试点名称排序，不使用的话可能会出现10排在2前面的情况。')
			natsort_warned = True
		return sorted

class Datum(dict):
	def __init__(self, datum, prob = None, key = 'data'):
		super(Datum, self).__init__(datum)
		self.prob = prob
		self.key = key
	def ml(self):
		return Memory(self['memory limit']) if 'memory limit' in self else self.prob.ml()

class Problem(Configure):
	def statement(self, cur_lang = None):
		if not cur_lang and lang:
			cur_lang = lang
		if cur_lang:
			source = pjoin(self.path, 'statement', cur_lang + '.md')
			if os.path.exists(source):
				self.language = cur_lang
				return source
		for source, self.language in (
			(pjoin(self.path, 'statement', 'zh-cn.md'), 'zh-cn'),
			(pjoin(self.path, 'statement', 'en.md'), 'en'),
			(pjoin(self.path, 'description.md'), None)
		):
			if os.path.exists(source):
				return source
		raise NoFileException('No md file found.')
	def lang(self):
		try:
			self.statement()
			return self.language
		except NoFileException as e:
			return None
	def __init__(self, *args):
		super(Problem, self).__init__(*args)
		self.chk = None
		self.data = self.get_data('data')
		self.samples = self.get_data('samples')
		self.pre = self.get_data('pre')
	def set_default(self, path = None):
		super(Problem, self).set_default(path)
		if 'title' not in self and 'cnname' in self:
			self['title'] = {'zh-cn' : self.pop('cnname')}
		for data, cases, attr, key in [('data', 'test cases', 'test_cases', 'data'), ('samples', 'sample count', 'sample_cases', 'down'), ('pre', 'pre count', 'pre_cases', 'pre')]:
			tc = set()
			if hasattr(self, data) and self.__getattribute__(data) != None:
				for datum in self.__getattribute__(data):
					tc |= set(datum['cases'])
			else:
				self[data] = []
			if cases in self and type(self[cases]) == int:
				log.warning(u'`%s`字段不再使用，使用`python -m tuack.gen upgrade`升级。' % cases)
				#to_dp = lambda i : DataPath({'case' : self['name'] + str(i), 'key' : key, 'depth' : 0, 'prefix' : self.path})
				#self[data] = [{'cases' : [
				#	to_dp(i) for i in range(1, self.pop(cases) + 1) \
				#	if to_dp(i) not in tc
				#]}]
			self.__setattr__(attr, sorter()(list(tc)))
	def set_score(self):
		if 'packed' in self:
			log.warning(u'题目`%s`的`packed`字段不再有效，但仍可以存在，用`python -m tuack.gen upgrade`升级。' % self.route)
		num_unscored = 0
		total_score = 0.0
		if not self.data:
			self.packed = False
			return
		for datum in self.data:
			if 'score' in datum:
				datum.score = datum['score']
				total_score += datum['score']
			else:
				num_unscored += 1
		if num_unscored != 0:
			item_score = (100. - total_score) / num_unscored
			for datum in self.data:
				if 'score' not in datum:
					datum.score = item_score
		if num_unscored == len(self.data):
			self.packed = False
			self.score = 100.
		else:
			self.packed = True
			if num_unscored != 0:
				log.warning(u'题目`%s`有%d个包设置了`score`，有%d个没有；总分共设%f分，将剩下%f分平分给没有的包。' % (
					self.route,
					len(self.data) - num_unscored,
					num_unscored,
					total_score,
					100 - total_score
				))
				log.info(u'如果你需要不等分+打包测试，请每个包设置`score`；否则请每个包都不设置`score`，此时是每个测试点同分而不是每个包同分。')
				log.info(u'一部分包设置`score`，另一部分不设置将可能导致导出其他格式时出现问题。')
				self.score = 100.0
			else:
				if abs(total_score - 100) > 1e-6:
					log.warning(u'题目`%s`总分是%f分，不是100分。' % (self.route, total_score))
				self.score = total_score

	def extend_pathed(self, path):
		if path.startswith(':'):
			return self.parent.extend_pathed(path[1:])
		return pjoin(self.path, path)

	def users(self):
		def users_pathed(self, users, key = '', depth = 0):
			if type(users) != dict:
				log.warning(u'`json.conf`中，`users`项%s:%s已经过时，但仍可以使用，用`python -m tuack.gen upgrade`升级' % (key, users))
				return {
					'path' : self.extend_pathed(users),
					'expected' : {}
				}
			elif depth == 2:
				# Is detailed description
				if "path" not in users:
					# Ill-formed
					log.warning(u'`users`项%s:%s不含`path`项' % (key, users))
					return None
				return {
					'path' : self.extend_pathed(users["path"]),
					'expected' : users["expected"] if "expected" in users else {}
				}

			return {
				key : val
				for key, val in \
				((key, users_pathed(self, val, key, depth + 1)) for key, val in users.items()) \
				if val
			}
		return self.getitem('users', users_pathed)
	
	def expect(self, user, algo, score):
		'''
		Check expected scores
		'''
		exp = self.users()[user][algo]['expected']
		algo_failed = False
		if type(exp) == dict:
			for symbol, value in exp.items():
				algo_failed |= not eval('score %s %s' % (symbol, value))
		elif type(exp) == list:
			for pred in exp:
				algo_failed |= not eval('score %s' % pred)
		elif type(exp) == str:
			algo_failed |= not eval('score %s' % exp)
		elif exp is None:
			pass
		else:
			log.warning('`expected`字段必须是字符串、数组或字典。')
		return not algo_failed

	def get_data(self, key):
		def data_pathed(self, data, key, depth):
			key_map = {
				'data' : 'data',
				'samples' : 'down',
				'pre' : 'pre'
			}
			ret = []
			for datum in data:
				tmp = []
				for case in datum['cases']:
					cur = self
					dep = depth
					cas = str(case)
					while cas.startswith(':'):
						cas = cas[1:]
						dep -= 1
						cur = cur.parent
					tmp.append(DataPath({'case' : cas, 'key' : key_map[key], 'depth' : dep, 'prefix' : cur.path}))
				datum_fixed = datum.copy()
				datum_fixed['cases'] = tmp
				ret.append(Datum(datum_fixed, self, key))
			return ret
		return self.getitem(key, data_pathed)

	def ml(self):
		return Memory(self.get('memory limit', '2 GB'))

	def memory_limit(self):
		return self.ml()

#mem_json = {}	# 题目复用的话，需要记忆化

def load_json(path = '.', route = None):
	#abs_path = os.path.abspath(path)
	#if abs_path in mem_json:
	#	return mem_json[abs_path]
	for name in ['conf.yaml', 'conf.json', 'prob.json']:
		try:
			full_path = pjoin(path, name)
			if os.path.isfile(full_path):
				inp = open(full_path, 'rb').read().decode('utf-8')
				if name.endswith('json'):
					conf = json.loads(inp)
				elif name.endswith('yaml'):
					conf = yaml.load(inp)
				if conf.get('version', -1) > json_version:
					log.warning(u'`conf.*`版本高于`tuack`，请升级`tuack`。')
				if 'folder' not in conf:
					conf['folder'] = 'problem'
				args = [conf, path]
				if conf['folder'] == 'extend':
					base_conf = load_json(pjoin(path, conf['base path']))
					folder = base_conf.folder
					args.append(base_conf)
				else:
					folder = conf['folder']
				conf = eval(folder.capitalize())(*args)
				if conf['folder'] == 'extend':
					conf.folder = base_conf.folder
				conf.set_default(os.path.basename(path))
				conf.route = '' if route == None else rjoin(route, conf['name'])
				if conf.folder == 'problem':
					conf.set_score()
				if 'subdir' in conf:
					conf.sub = [
						load_json(pjoin(path, sub), conf.route) \
						for sub in conf['subdir']
					]
				#mem_json[abs_path] = conf
				return conf
		except Exception as e:
			log.error(u'文件`%s`错误或子目录下文件错误。' % pjoin(path, name))
			log.info(e)
			raise e
	else:
		raise NoFileException(u'路径`%s`下找不到conf.*。' % path)

def del_redundance(conf, red):
	for key in red:
		try:
			conf.pop(key)
		except:
			pass
	if not conf['name'] or conf['name'] == '.':
		conf.pop('name')
	return conf

dump_formats = {
	'json' : lambda conf : json.dumps(conf, indent = 2, sort_keys = True, ensure_ascii = False).encode('utf-8'),
	'yaml' : lambda conf : yaml.safe_dump(dict(conf), encoding = 'utf-8', allow_unicode = True)
}

def save_json(conf):
	for s in conf.sub:
		save_json(s)
	try:
		open(pjoin(conf.path, 'conf.' + dump_format), 'wb').write(dump_formats[dump_format](conf))
	except Exception as e:
		log.error(u'不支持配置文件格式`%s`。' % dump_format)
		log.info(e)

def any_prefix(pre, st = None):
	if not st:
		st = sub_set
	for s in st:
		if s == pre:
			return 1
		if pre == '' or s.startswith(pre + '/'):
			return 2
	return 0

def mkdir(name):
	if not os.path.exists(name):
		os.makedirs(name)

def remkdir(name):
	while True:
		try:
			shutil.rmtree(name, ignore_errors = True)
			time.sleep(0.1)
			if not os.path.exists(name):
				os.makedirs(name)
			break
		except Exception as e:
			log.warning('Can\'t delete %s' % name)
			log.warning(e)

def copy(source, name, target):
	full_source = pjoin(source, name)
	if not os.path.exists(full_source):
		raise NoFileException('No such file or path `%s`.' % full_source)
	copied_data.add(full_source)
	if os.path.isdir(full_source):
		if full_source.endswith('.dir') or no_compiling:
			full_target = (pjoin(target, name) if os.path.exists(target) else target)
			if full_source.endswith('.dir'):
				full_target = full_target[:-4]
			shutil.copytree(full_source, full_target)
		else:
			# TODO: make if there is a makefile
			ret = os.getcwd()
			os.chdir(pjoin(source, name))
			cpp_file = name + '.cpp'
			elf_file = name + elf_suffix
			check_install('g++')
			if os.system('g++ %s -o %s -O2 -std=c++14 -Wall' % (cpp_file, elf_file)) != 0:
				os.chdir(ret)
				log.error(u'`%s`编译失败。' % pjoin(full_source, cpp_file))
				return True
			else:
				os.chdir(ret)
				log.info(u'`%s`编译成功。' % pjoin(full_source, cpp_file))
			shutil.move(pjoin(full_source, elf_file), target)
	else:
		shutil.copy(full_source, target)
	return True

def xopen_file(path):
	try:
		if system == 'Windows':
			os.startfile(path)
		elif system == 'Darwin':
			subprocess.call(["open", path])
		else:
			subprocess.call(["xdg-open", path])
	except Exception as e:
		log.warning(u'打开文件`%s`失败。' % path)
		log.info(e)

def deal_args():
	global do_copy_files, do_test_progs, do_release, works, start_file, do_pack, langs, lang, sub_set, out_system, args, do_zip, do_encript, do_render, time_multiplier, git_lfs, dump_format, user_time
	do_render = True
	works = []
	args = []
	langs = [None]
	lang = None
	sub_set = None
	start_file = True
	do_pack = True
	do_zip = False
	do_encript = False
	git_lfs = False
	user_time = False
	dump_format = 'yaml'
	l = len(sys.argv)
	i = 1
	while i < l:
		if sys.argv[i] == '-i':
			i += 1
			os.chdir(sys.argv[i])
		elif sys.argv[i] == '-p':
			i += 1
			sub_set = set(sys.argv[i].split(','))
		elif sys.argv[i] == '-o':
			i += 1
			out_system = sys.argv[i]
		elif sys.argv[i] == '-d':
			i += 1
			dump_format = sys.argv[i]
		elif sys.argv[i] == '-s':
			start_file = False
		elif sys.argv[i] == '-k':
			do_pack = False
		elif sys.argv[i] == '-z':
			do_zip = True
		elif sys.argv[i] == '-g':
			git_lfs = True
		elif sys.argv[i] == '-r':
			do_render = False
		elif sys.argv[i] == '-e':
			do_zip = True
			do_encript = True
		elif sys.argv[i] == '-u':
			user_time = True
		elif sys.argv[i] == '-l':
			i += 1
			langs = set(sys.argv[i].split(','))
		elif sys.argv[i] == '-t':
			i += 1
			time_multiplier = float(sys.argv[i])
		elif sys.argv[i] == '-h' or sys.argv[i] == '--help':
			log.info(u'详细用法见文档：https://git.thusaac.org/publish/tuack/wikis。')
			log.info(u'python 脚本 [[[工作1],工作2],...] [[[选项1] 选项2] ...] [[[参数1] 参数2] ...]')
			log.info(u'工作必须在参数前面，工作用逗号隔开，选项和参数用空格隔开。')
			log.info(u'只有有逗号的项目可以用逗号获得多个结果，逗号前后不能有空白符。')
			log.info(u'这套工具的大多数脚本都可以在比赛、比赛日和题目目录下运行。')
			log.info(u'选项：')
			log.info(u'  -i PATH             指定PATH作为工作路径，否则使用当前路径。')
			log.info(u'  -s                  对于有输出的文件的操作，输出完以后不自动打开文件。')
			log.info(u'  -p day0/sleep,day2  只对day0/sleep和day2进行本次操作；此路径是基于当前文件夹的，')
			log.info(u'                      例如：在比赛日目录如day1下，则可以直接指定题目如exam；')
			log.info(u'                      对于test，还可以指定用户或算法，如day1/problem/vfk/std.cpp。')
			log.info(u'  -t 6.0              对于test，设置掐断时间为6.0*时间限制，用于对比不同程序的时限。')
			log.info(u'  -o SYSTEM           对于ren，输出指定操作系统的题面，可选Windows和Linux。')
			log.info(u'  -l zh-cn,en         对于ren，指定输出语言，不指定默认为zh-cn。')
			log.info(u'  -r                  对于dump，不先尝试渲染题面。')
			log.info(u'  -g                  对于gen，使用git-lfs。')
			log.info(u'  -d json             对于gen，规定配置文件格式，支持json、yaml，默认yaml。')
			log.info(u'  -u                  对于test，在linux下使用user time做测试，默认real time。')
			return False
		else:
			if len(works) == 0:
				works = sys.argv[i].split(',')
			else:
				args += sys.argv[i].split(',')
		i += 1
	return True

def custom_conf():
	get_tool_conf()
	c = env_conf['file_log'] if 'file_log' in env_conf else {}
	file_log = logging.FileHandler(
		c['path'] if 'path' in c else 'tuack.log',
		mode = c['mode'] if 'mode' in c else 'a',
		encoding = c['encoding'] if 'encoding' in c else None
	)
	file_log.setLevel(c['level'] if 'level' in c else logging.INFO)
	file_log.setFormatter(logging.Formatter(
		c['format'] if 'format' in c else '[%(levelname).1s]%(filename)s:%(funcName)s:%(lineno)d:%(message)s'
	))
	log.addHandler(file_log)

	c = env_conf['bash_log'] if 'bash_log' in env_conf else {}
	if 'encoding' in c:
		class MyStream(object):
			def __init__(self, stream):
				self.stream = stream
			def write(self, s):
				self.stream.buffer.write(s.encode(c['encoding']))
				self.stream.flush()
			def flush(self):
				self.stream.flush()
		bash_log = logging.StreamHandler(MyStream(sys.stdout))
	else:
		bash_log = logging.StreamHandler()
	bash_log.setLevel(c['level'] if 'level' in c else logging.DEBUG)
	bash_log.setFormatter(logging.Formatter(
		c['format'] if 'format' in c else '[%(levelname).1s]%(message)s'
	))
	log.addHandler(bash_log)

def init():
	import __main__
	global conf
	custom_conf()
	if not deal_args():
		return False
	log.info(
		('脚本%s，工程路径%s，参数%s，开始于%s。' if python_version == 2 else u'脚本%s，工程路径%s，参数%s，开始于%s。') % (
			__main__.__file__, os.getcwd(), str(sys.argv[1:]), str(datetime.datetime.now())
		)
	)
	conf = load_json()
	try:
		check_install('git')
		check_install('git_lfs')
	except:
		pass
	return True

def tr(item):
	if 'zh-cn' in item:
		return item['zh-cn']
	elif 'en' in item:
		return item['en']
	elif len(item) > 1:
		for val in item.values():
			return val
	else:
		return 'Unknown'

def run_r(cmd, path):
	for f in os.listdir(path):
		cpath = pjoin(path, f)
		if os.path.isfile(cpath):
			cmd(cpath)
		else:
			run_r(cmd, cpath)

def get_tool_conf():
	def get_sys_env():
		return '$'.join([
			os.environ[key]
			for key in ['OS', 'SESSIONNAME', 'USERNAME', 'COMPUTERNAME', 'USERDOMAIN', 'USER', 'SHELL', 'SESSION'] \
			if key in os.environ
		] + ['py%x' % sys.hexversion])
	global env_conf
	try:
		tool_conf = json.loads(open(pjoin(tool_path, 'conf.json'), 'rb').read().decode('utf-8'))
	except:
		tool_conf = {}
	sys_env = get_sys_env()
	if sys_env not in tool_conf:
		tool_conf[sys_env] = {}
	env_conf = tool_conf[sys_env]
	return tool_conf

def check_install(pack):
	def check_import(pack, extra_info = '', pack_name = None, level = logging.ERROR):
		try:
			__import__(pack)
		except Exception as e:
			log.log(level, u'python包%s没有安装，使用 pip install %s 安装。%s' % (pack, pack_name if pack_name else pack, extra_info))
			if system == 'Windows':
				log.info(u'如果pip没有安装，Windows下推荐用Anaconda等集成环境。')
			if system == 'Linux':
				log.info(u'如果pip没有安装，Ubuntu下用 sudo apt install python-pip 安装。')
			raise e
	check_pyside = lambda : check_import('PySide', u'注意这个包只能在 python2 下使用。', 'pyside')
	check_jinja2 = lambda : check_import('jinja2')
	check_natsort = lambda : check_import('natsort', level = logging.WARNING)
	check_gettext = lambda : check_import('gettext')
	def check_pandoc():
		ret = os.system('pandoc -v')
		if ret != 0:
			log.error(u'格式转换工具pandoc没有安装。')
			if system == 'Windows':
				log.info(u'Windows用户去官方网站下载安装，安装好后把pandoc.exe所在路径添加到环境变量PATH中。')
			if system == 'Linux':
				log.info(u'Ubuntu下用 sudo apt install pandoc 安装。')
			raise Exception('pandoc not found')
	def check_xelatex():
		ret = os.system('xelatex --version')
		if ret != 0:
			log.error(u'TeX渲染工具XeLaTeX没有安装。')
			if system == 'Windows':
				log.info(u'Windows下可以先安装MiKTeX，在首次运行的时候会再提示安装后续文件。')
			if system == 'Linux':
				log.info(u'Ubuntu下先用 sudo apt install texlive-xetex texlive-fonts-recommended texlive-latex-extra 安装工具；')
				log.info(u'然后一般会因为缺少有些字体而报错（Windows有使用权，但Ubuntu没有，所以没有预装这些字体）。')
				log.info(u'可以使用下列页面上的方法安装缺少的字体或是把win下的字体复制过来。')
				log.info(u'http://linux-wiki.cn/wiki/zh-hans/LaTeX%E4%B8%AD%E6%96%87%E6%8E%92%E7%89%88%EF%BC%88%E4%BD%BF%E7%94%A8XeTeX%EF%BC%89')
			raise Exception('xelatex not found')
	def check_git():
		ret = os.system('git --version')
		if ret != 0:
			log.warning(u'版本管理工具git没有安装，如果工程用git维护则你的修改可能无法成功提交。')
			log.info(u'一个可能的安装教程见这里：')
			log.info(u'https://git-scm.com/book/zh/v2/%E8%B5%B7%E6%AD%A5-%E5%AE%89%E8%A3%85-Git')
			if system == 'Windows':
				log.info(u'Windows下有多种不同的git版本，大家可以多交流好用的版本。')
			log.info(u'git入门可以参看这里：')
			log.info(u'http://rogerdudler.github.io/git-guide/index.zh.html')
			log.info(u'一般推荐用ssh方式克隆仓库，并用公私钥保证安全，添加密钥的方式一般仓库的git网页上能找到。')
			raise Exception('git not found')
	def check_git_lfs():
		ret = os.system('git lfs')
		if ret != 0:
			log.warning(u'git大文件系统lfs没有安装，如果工程使用了它你可能无法同步。')
			log.info(u'因为有些评测数据比较大，所以一般要求用git lfs大文件系统（Large File System）管理评测数据（in/ans）')
			log.info(u'一个可能的安装教程见这里：')
			log.info(u'https://git-lfs.github.com/')
			log.info(u'如果你用本工具的generator生成题目工程，那么你装好lfs以后一般可以不用再手工指定in和ans文件用lfs管理。')
			log.info(u'如果你的多人合作工程用到了lfs，请务必不要在没有安装lfs前把数据添加到工程中！')
			raise Exception('git lfs not found')

	def check_gpp():
		ret = os.system('g++ -v')
		if ret != 0:
			log.warning(u'g++未安装，将可能无法测试C++代码。')
			raise Exception('g++ not found')
	
	def check_gcc():
		ret = os.system('gcc -v')
		if ret != 0:
			log.warning(u'gcc未安装，将可能无法测试C代码。')
			raise Exception('gcc not found')
			
	def check_java():
		ret = os.system('javac -version')
		if ret != 0:
			log.warning(u'javac未安装，将可能无法测试Java代码。')
			raise Exception('javac not found')
		ret = os.system('java -version')
		if ret != 0:
			log.warning(u'java未安装，将可能无法测试Java代码。')
			raise Exception('java not found')

	def check_py2():
		ret = os.system('python2 --version')
		if ret != 0:
			log.warning(u'python2未安装，将可能无法测试Python2代码。')
			raise Exception('python2 not found')

	def check_py3():
		ret = os.system('python3 --version')
		if ret != 0:
			log.warning(u'python3未安装，将可能无法测试Python3代码。')
			raise Exception('python3 not found')

	def check_py():
		ret = os.system('python --version')
		if ret != 0:
			log.warning(u'python未安装，将可能无法测试Python代码。')
			raise Exception('python not found')
			
	def check_flex():
		ret = os.system('flex --version')
		if ret != 0:
			log.warning(u'flex未安装，将可能无法检查题面格式。')
			raise Exception('flex not found')

	def check_bison():
		ret = os.system('bison --version')
		if ret != 0:
			log.warning(u'bison未安装，将可能无法检查题面格式。')
			raise Exception('bison not found')
			
	def check_format():
		ret = os.system('%s -v' % pjoin(tool_path, format_checker_name))
		if ret != 0:
			log.warning(u'format checker未安装，使用`python -m tuack.install format`安装。')
			raise Exception('format not found')

	if pack in {'g++', 'cpp'}:
		pack = 'gpp'
	if pack == 'c':
		pack = 'gcc'
	tool_conf = get_tool_conf()
	if 'installed' not in env_conf:
		env_conf['installed'] = {}
	if pack in env_conf['installed'] and env_conf['installed'][pack]:
		return True
	eval('check_' + pack)()
	env_conf['installed'][pack] = True

	open(pjoin(tool_path, 'conf.json'), 'wb').write(json.dumps(tool_conf, indent = 2, sort_keys = True).encode('utf-8'))
	return True

def change_eol(path, eol):
	import uuid
	ufname = str(uuid.uuid4()) + '.tmp'
	space_end = False
	is_text = True
	with open(ufname, 'wb') as f:
		try:
			for idx, line in enumerate(open(path, 'rb')):
				line = line.rstrip(b'\r\n')
				f.write(line + eol)
				if not space_end and (line.endswith(b' ') or line.endswith(b'\t')):
					log.warning(u'换行符转换：文件`%s`第%d行末尾有空白符。' % (path, idx + 1))
					space_end = True
				for code in ['utf-8', 'gbk']:
					try:
						if '\0' in line.decode(code):
							raise Exception('`\\0` in line')
						break
					except:
						pass
				else:
					is_text = False
					log.info(u'换行符转换：文件`%s`不是文本文件。' % path)
					break
		except:
			is_test = False
	if is_text:
		os.remove(path)
		os.rename(ufname, path)
	else:
		os.remove(ufname)

unix2dos = lambda path : change_eol(path, b'\r\n')
dos2unix = lambda path : change_eol(path, b'\n')

wiki = lambda name : name

def run_exc(func):
	try:
		return (True, func())
	except Exception as e:
		log.error(e)
		log.info(traceback.format_exc())
		return (False, None)
