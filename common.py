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
windows_stack_size = 536870912
diff_tool = 'diff' if system != 'Windows' else 'fc'
time_multiplier = 3.
elf_suffix = '' if system != 'Windows' else '.exe'
problem_skip = re.compile(r'^(data|down|tables|resources|gen)$')
user_skip = re.compile(r'^(val|gen|chk|checker|report|.*\.test|.*\.dir)$')
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

def load_problems():
	problem_names = json.load(open('probs.json'))
	probs = {}
	for day, names in problem_names.items():
		problems = []
		for name in names:
			try:
				problem = json.loads(open(os.path.join(day, name, 'prob.json'), 'rb').read().decode('utf-8'))
				problem['name'] = name
				problems.append(problem)
			except Exception as e:
				print('At %s/%s.' % (day, name))
				raise e
		probs[day] = problems
	return probs

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
	full_source = os.path.join(source, name)
	if not os.path.exists(full_source):
		return False
	copied_data.add(full_source)
	if os.path.isdir(full_source):
		if full_source.endswith('.dir') or no_compiling:
			full_target = (os.path.join(target, name) if os.path.exists(target) else target)
			if full_source.endswith('.dir'):
				full_target = full_target[:-4]
			shutil.copytree(full_source, full_target)
		else:
			# TODO: make if there is a makefile
			ret = os.getcwd()
			os.chdir(os.path.join(source, name))
			cpp_file = name + '.cpp'
			elf_file = name + elf_suffix
			if os.system('g++ %s -o %s -O2' % (cpp_file, elf_file)) != 0:
				os.chdir(ret)
				error('Can\'t compile \'%s\'' % os.path.join(full_source, cpp_file))
				return True
			else:
				os.chdir(ret)
				infom('\'%s\' compile succeeded.' % os.path.join(full_source, cpp_file))
			shutil.move(os.path.join(full_source, elf_file), target)
	else:
		shutil.copy(full_source, target)
	return True

def compile(prob):
	for lang, args in prob['compile'].items():
		if os.path.exists(os.path.join('tmp', prob['name'] + '.' + lang)):
			os.chdir('tmp')
			ret = subprocess.call(compilers[lang](prob['name'], args, macros[work]), shell = True, stdout = open('log', 'w'), stderr = subprocess.STDOUT)
			os.chdir('..')
			return '`' + prob['name'] + '.' + lang + '` compile failed.' if ret != 0 else None
	else:
		return 'Can\'t find source file.'
	return None
	
def deal_argv():
	global do_copy_files, do_test_progs, do_release, day_set, prob_set, probs, works, start_file, user_set, algo_set, do_pack
	works = []
	day_set = None
	prob_set = None
	user_set = None
	algo_set = None
	start_file = True
	do_pack = True
	l = len(sys.argv)
	i = 1
	while i < l:
		if sys.argv[i] == '-i':
			i += 1
			os.chdir(sys.argv[i])
		elif sys.argv[i] == '-d':
			i += 1
			day_set = set(sys.argv[i].split(','))
		elif sys.argv[i] == '-p':
			i += 1
			prob_set = set(sys.argv[i].split(','))
		elif sys.argv[i] == '-u':
			i += 1
			user_set = set(sys.argv[i].split(','))
		elif sys.argv[i] == '-a':
			i += 1
			algo_set = set(sys.argv[i].split(','))
		elif sys.argv[i] == '-s':
			start_file = False
		elif sys.argv[i] == '-k':
			do_pack = False
		elif sys.argv[i] == '-h' or sys.argv[i] == '--help':
			print('Options:')
			print('\t-i PATH: Specify a path to work. Otherwise, use current path.')
			print('\t-s: Do not open result files when finished.')
			print('\t-d day0,day2: Only do those work for day0 and day2.')
			print('\t-p day0/sleep,day2/nodes: Only do those work for day0/sleep and day2/nodes.')
			print('\tDo not use -d and -p together.')
			return False
		else:
			works += sys.argv[i].split(',')
		i += 1
	probs = load_problems()
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
	return True
