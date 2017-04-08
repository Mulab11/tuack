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

work = None
system = platform.system()
out_system = system
windows_stack_size = 536870912
diff_tool = 'diff' if system != 'Windows' else 'fc'
time_multiplier = 3.
elf_suffix = '' if system != 'Windows' else '.exe'
problem_skip = re.compile(r'^(data|down|tables|resources|gen)$')
user_skip = re.compile(r'^(data|down|val|gen|chk|checker|report|check|make_data|make|generate|generator|makedata|.*\.test|.*\.dir)$')
compilers = {
	'cpp' : lambda name, args, macros = '': 'g++ %s.cpp -o %s %s %s %s' % (name, name, args, macros, '' if system != 'Windows' else '-Wl,--stack=%d' % windows_stack_size),
	'c' : lambda name, args, macros = '': 'gcc %s.c -o %s %s %s %s' % (name, name, args, macros, '' if system != 'Windows' else '-Wl,--stack=%d' % windows_stack_size),
	# I don't know how to change stack size, add #define in pascal
	'pas' : lambda name, args, macros = '': 'fpc %s.pas %s' % (name, args)
}
macros = {
	'uoj' : '-DONLINE_JUDGE',
	'noi' : '-D__ARBITER__',
	'release' : '',
	'test' : '-D__OI_TESTER__'
}

frep = open('tester.log', 'a')
copied_data = set()
no_compiling = False
path = os.path.dirname(os.path.realpath(__file__))

def infom(info):
	frep.write('[I]' + info + '\n')

def warning(info):
	frep.write('[W]' + info + '\n')

def error(info):
	frep.write('[E]' + info + '\n')

def fatal(info):
	frep.write('[E]' + info + '\n')
	frep.close()
	sys.exit(info)

def memory2bytes(st):	
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
	sp = st.split(' ')
	un = (units[sp[1]] if len(sp) == 2 else 1)
	return int(sp[0]) * un
	
'''
def set_default(prob, name):
	if 'name' not in prob:
		prob['name'] = name
	if 'test cases' not in prob:
		prob['test cases'] = sum((len(datum['cases']) for datum in prob['data']))
	if 'packed' in prob and prob['packed']:
		num_unscored = 0
		total_score = 0.0
		for datum in prob['data']:
			if 'score' in datum:
				total_score += datum['score']
			else:
				num_unscored += 1
		if num_unscored == 0:
			return
		item_score = (100. - total_score) / num_unscored
		for datum in prob['data']:
			if 'score' not in datum:
				datum['score'] = item_score
'''

pjoin = lambda *args : os.path.join(*args).rstrip('/').rstrip('\\')
rjoin = lambda *args : '/'.join(args).strip('/')

def set_default_problem(conf, path = None):
	conf['all'] = True
	if 'title' not in conf and 'cnname' in conf:
		conf['title'] = {'zh-cn' : conf['cnname']}
	if 'test cases' in conf and type(conf['test cases']) == int:
		conf['test cases'] = list(range(1, conf['test cases'] + 1))
	elif 'data' in conf:
		tc = set()
		for datum in conf['data']:
			tc |= set(datum['cases'])
		conf['test cases'] = sorted(map(str, list(tc)))
	if 'samples' not in conf:
		if 'sample count' in conf:
			conf['samples'] = [{'cases' : list(range(1, conf['sample count'] + 1))}]
		else:
			conf['samples'] = []
	tc = set()
	for datum in conf['samples']:
		tc |= set(datum['cases'])
	try:
		conf['sample cases'] = sorted(list(tc))
	except:
		conf['sample cases'] = sorted(map(str, list(tc)))
	if 'name' not in conf:
		conf['name'] = path
	if 'packed' in conf and conf['packed']:
		num_unscored = 0
		total_score = 0.0
		for datum in conf['data']:
			if 'score' in datum:
				total_score += datum['score']
			else:
				num_unscored += 1
		if num_unscored != 0:
			item_score = (100. - total_score) / num_unscored
			for datum in conf['data']:
				if 'score' not in datum:
					datum['score'] = item_score
	return conf
	
def set_default_day(conf, path = None):
	conf['all'] = True
	if 'name' not in conf:
		conf['name'] = path
	return conf

def set_default_contest(conf, path = None):
	conf['all'] = True
	if 'name' not in conf:
		conf['name'] = path
	return conf
	
'''
def load_problems():
	problem_names = json.load(open('probs.json'))
	probs = {}
	for day, names in problem_names.items():
		problems = []
		for name in names:
			try:
				problem = json.loads(open(os.path.join(day, name, 'prob.json'), 'rb').read().decode('utf-8'))
				set_default(problem, name)
				problems.append(problem)
			except Exception as e:
				print('At %s/%s.' % (day, name))
				raise e
		probs[day] = problems
	return probs
'''

def extend_merge(base, ext):
	for key, val in ext.items():
		if key == 'path' or key == 'folder':
			continue
		elif key.endswith('+'):
			k = key[:-1]
			if type(base[k]) == type(val) == dict:
				base[k] = extend_merge(base[k], val)
			elif type(base[k]) == type(val) == list:
				base[k] += val
			else:
				raise Exception('extend error %s' % key)
		else:
			base[key] = val
	return base
	
class NoJsonException(Exception):
	pass
	
def load_json(path = '.', route = None):
	for name in ['conf.json', 'prob.json']:
		try:
			full_path = pjoin(path, name)
			if os.path.exists(full_path):
				conf = json.loads(open(full_path, 'rb').read().decode('utf-8'))
				if 'folder' not in conf:
					conf['folder'] = 'problem'
				if conf['folder'] == 'extend':
					base_conf = load_json(pjoin(path, conf['base path']))
					conf = extend_merge(base_conf, conf)
					#print(conf)
					path = base_conf['path']
				else:
					conf['path'] = path
				conf = eval('set_default_' + conf['folder'])(conf, os.path.basename(path))
				conf['route'] = '' if route == None else rjoin(route, conf['name'])
				if 'subdir' in conf:
					conf['sub'] = [
						load_json(pjoin(path, sub), conf['route']) \
						for sub in conf['subdir']
					]
				return conf
		except Exception as e:
			print('Error at json configure file `%s`.' % pjoin(path, name))
			raise e
	else:
		raise NoJsonException('Can\'t find configure json file at `%s`.' % path)

def del_redundance(conf, red):
	for key in red:
		try:
			conf.pop(key)
		except:
			pass
	if not conf['name'] or conf['name'] == '.':
		conf.pop('name')
	return conf
	
redundances = {
	'problem' : ['test cases', 'sample cases', 'sample count'],
	'day' : [],
	'contest' : []
}

common_redundances = ['all', 'path', 'route']
		
def save_json(conf):
	if 'base path' in conf:
		warning('extend folder type can\'t use generate.')
		return
	cp = conf.copy()
	if 'sub' in cp:
		sub = cp.pop('sub')
		for s in sub:
			save_json(s)
	cp = del_redundance(cp, redundances[cp['folder']] + common_redundances)
	open(pjoin(conf['path'], 'conf.json'), 'wb').write(
		json.dumps(cp, indent = 2, sort_keys = True).encode('utf-8')
	)
		
def any_prefix(pre, st = None):
	if not st:
		st = sub_set
	for s in st:
		if s.startswith(pre):
			return True
	return False
		
def probs(item = None, pick = False):
	if not item:
		item = conf
	pick |= not sub_set or item['route'] in sub_set
	if item['folder'] == 'problem':
		if pick or any_prefix(item['route']):
			item['all'] = pick
			yield item
	else:
		for sub in item['sub']:
			for prob in probs(sub, pick):
				yield prob
				
def days(item = None, pick = False):
	if not item:
		item = conf
	pick |= not sub_set or item['route'] in sub_set
	if item['folder'] == 'problem':
		return
	if item['folder'] == 'day':
		if pick or any_prefix(item['route']):
			item['all'] = pick
			yield item
	else:
		for sub in item['sub']:
			for day in days(sub, pick):
				yield day

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
			print(e)
			warning('Can\'t delete %s' % name)
		
def copy(source, name, target):
	full_source = pjoin(source, name)
	if not os.path.exists(full_source):
		raise Exception('No such file or path `%s`.' % full_source)
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
			if os.system('g++ %s -o %s -O2' % (cpp_file, elf_file)) != 0:
				os.chdir(ret)
				error('Can\'t compile \'%s\'' % pjoin(full_source, cpp_file))
				return True
			else:
				os.chdir(ret)
				infom('\'%s\' compile succeeded.' % pjoin(full_source, cpp_file))
			shutil.move(pjoin(full_source, elf_file), target)
	else:
		shutil.copy(full_source, target)
	return True
	
def deal_args():
	global do_copy_files, do_test_progs, do_release, probs, works, start_file, do_pack, langs, sub_set, out_system, args
	works = []
	args = []
	langs = ['zh-cn']
	sub_set = None
	start_file = True
	do_pack = True
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
		elif sys.argv[i] == '-s':
			start_file = False
		elif sys.argv[i] == '-k':
			do_pack = False
		elif sys.argv[i] == '-l':
			i += 1
			langs = set(sys.argv[i].split(','))
		elif sys.argv[i] == '-h' or sys.argv[i] == '--help':
			print('Options:')
			print('\t-i PATH: Specify a path to work. Otherwise, use current path.')
			print('\t-s: Do not open result files when finished.')
			print('\t-p day0/sleep,day2: Only do those work for day0/sleep and day2.')
			return False
		else:
			if len(works) == 0:
				works = sys.argv[i].split(',')
			else:
				args += sys.argv[i].split(',')
		i += 1
	# if -p or -d is not set, use all of the problems or days
	'''
	if not prob_set:
		prob_set = set()
		for day, info in probs.items():
			for prob in info:
				prob_set.add(day + '/' + prob['name'])
	if not day_set:
		if not prob_set:
			day_set = set(probs.keys())
		else:
			day_set = {prob.split('/')[0] for prob in prob_set}
	'''
	return True
	
def init():
	global conf
	if not deal_args():
		return False
	conf = load_json()
	#print(json.dumps(conf))
	return True
