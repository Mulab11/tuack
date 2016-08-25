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

system = platform.system()
windows_stack_size = 536870912
diff_tool = 'diff' if system != 'Windows' else 'fc'
time_multiplier = 3.
elf_suffix = '' if system != 'Windows' else '.exe'
copied_data = set()
problem_skip = re.compile(r'^(data|down)$')
user_skip = re.compile(r'^(val|gen|chk|checker|report|.*\.test|.*\.dir)$')
compilers = {
	'cpp' : lambda name, args: 'g++ %s.cpp -o %s %s %s -D__OI_TESTER__' % (name, name, args, '' if system != 'Windows' else '-Wl,--stack=%d' % windows_stack_size),
	'c' : lambda name, args: 'gcc %s.c -o %s %s %s %s -D__OI_TESTER__' % (name, name, args, '' if system != 'Windows' else '-Wl,--stack=%d' % windows_stack_size),
	# I don't know how to change stack size in pascal
	'pas' : lambda name, args: 'fpc %s.pas %s' % (name, args)
}
doc_format = re.compile(r'^(.*)\.(doc|docs|ppt|pptx|pdf|tex|md|html|htm|zip|dir)$')

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
	
def remkdir(name):
	shutil.rmtree(name, ignore_errors = True)
	time.sleep(0.1)
	if not os.path.exists(name):
		os.makedirs(name)
	
def find_doc(path, name):
	for f in os.listdir(path):
		m = doc_format.match(f)
		if m and m.group(1) == name:
			return name, '.' + m.group(2)
	return None
	
def copy_one_day_files(probs, day_name):
	remkdir('data')
	print('copy data files')
	for prob in probs:
		if day_name + '/' + prob['name'] not in prob_set:
			continue
		# TODO: if test cases is a list of scores instead of an integer
		data_path = os.path.join(prob['name'], 'data')
		for i in range(1, prob['test cases'] + 1):
			for suf in ['.in', '.ans']:
				copy(data_path, prob['name'] + str(i) + suf, 'data')
		copy(data_path, 'chk', os.path.join('data', prob['name'] + '_e'))
		for name in os.listdir(data_path):
			if os.path.join(data_path, name) not in copied_data:
				warning('Unusual file \'%s\' found.' % os.path.join(data_path, name))
				copy(data_path, name, 'data')
	print('dos2unix data files')
	if os.system('dos2unix data/* 2> log') != 0:
		warning('dos2unix failed.')
	print('copy down files')
	remkdir('down')
	for prob in probs:
		if day_name + '/' + prob['name'] not in prob_set:
			continue
		# TODO: if test cases is a list of scores instead of an integer
		data_path = os.path.join(prob['name'], 'down')
		target_path = os.path.join('down', prob['name'])
		if not os.path.exists(target_path):
			os.makedirs(target_path)
		case_no = (prob['test cases'] if prob['type'] == 'output' else prob['sample count'])
		suffices = (['.in'] if prob['type'] == 'output' else ['.in', '.ans'])
		for i in range(1, case_no + 1):
			for suf in suffices:
				copy(data_path, prob['name'] + str(i) + suf, target_path)
		copy(data_path, 'checker', target_path)
		for name in os.listdir(data_path):
			if os.path.join(data_path, name) not in copied_data:
				warning('Unusual file \'%s\' found.' % os.path.join(data_path, name))
				copy(data_path, name, target_path)
	print('dos2unix down files')
	for prob in probs:
		if os.system('dos2unix %s/%s/* 2> log' % ('down', prob['name'])) != 0:
			warning('dos2unix failed.')
			break
	remkdir('discussion')
	for prob in probs:
		res = find_doc(prob['name'], 'discussion')
		if res:
			copy(prob['name'], res[0] + res[1], os.path.join('discussion', prob['name'] + res[1]))
		else:
			warning('Can\'t find discussion ppt for problem `%s`.' % prob['name'])
	if os.path.exists('log'):
		os.remove('log')
	
def copy_files():
	for day_name, day_data in probs.items():
		if day_name not in day_set:
			continue
		os.chdir(day_name)
		copy_one_day_files(day_data, day_name)
		os.chdir('..')
	
def compile(prob):
	for lang, args in prob['compile'].items():
		if os.path.exists(os.path.join('tmp', prob['name'] + '.' + lang)):
			os.chdir('tmp')
			ret = subprocess.call(compilers[lang](prob['name'], args), shell = True, stdout = open('log', 'w'), stderr = subprocess.STDOUT)
			os.chdir('..')
			return '`' + prob['name'] + '.' + lang + '` compile failed.' if ret != 0 else None
	else:
		return 'Can\'t find source file.'
	return None
	
def run_windows(name, tl, ml):
	t = time.clock()
	try:
		pro = subprocess.Popen(name, startupinfo = subprocess.SW_HIDE)
	except:
		return 'Can\'t run program.', 0.0
	while True:
		ret = pro.poll()
		if ret != None:
			t = time.clock() - t
			if ret == 0:
				ret = None
			else:
				ret = 'Runtime error %d.' % ret
			break
		if (time.clock() - t) >= tl * time_multiplier:
			pro.kill()
			t = 0.0
			ret = 'Time out.'
			break
		time.sleep(1e-2)
	time.sleep(1e-2)
	return ret, t

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

def runner_linux(name, que, ml):
	pro = subprocess.Popen(
		'ulimit -v %d; time -f "%%U" -o timer ./%s' % (memory2bytes(ml) // 1024, name),
		shell = True,
		preexec_fn = os.setsid
	)
	que.put(pro.pid)
	ret = pro.wait()
	que.put(ret)
	
def run_linux(name, tl, ml):
	'''
	Memory limit is not considered.
	'''
	que = Queue()
	pro = Process(target = runner_linux, args = (name, que, ml))
	pro.start()
	pro.join(tl * time_multiplier)
	if que.qsize() == 0:
		fatal('Runner broken.')
	elif que.qsize() == 1:
		ret = 'time out.'
		pid = que.get()
		#print('pid = %d' % pid)
		os.killpg(os.getpgid(pid), signal.SIGTERM)
		t = 0.
	else:
		pid = que.get()
		ret = que.get()
		if ret == 0:
			try:
				t = float(open('timer').readline())
			except:
				warning('Timer broken.')
				t = 0.
			ret = None
		else:
			ret = 'Runtime error %d.' % ret
			t = 0.
	return ret, t

if system == 'Linux':
	run = run_linux
elif system == 'Windows':
	run = run_windows
	
def test(prob):
	scores = []
	times = []
	reports = []
	if prob['type'] == 'program':
		res = compile(prob)
		if res:
			for i in range(prob['test cases'] + prob['sample count']):
				scores.append(0.0)
				times.append(0.0)
				reports.append(res)
			return scores, times, reports
	all_cases = [
		('data', i) for i in range(1, prob['test cases'] + 1)
	] + [
		(os.path.join('down', prob['name']), i) for i in range(1, prob['sample count'] + 1)
	]
	for path, i in all_cases:
		print('Case %s:%d' % (path, i), end = '\r')
		shutil.copy(os.path.join(path, prob['name'] + str(i) + '.in'), os.path.join('tmp', prob['name'] + '.in'))
		if prob['type'] == 'program':
			os.chdir('tmp')
			ret, time = run(prob['name'], prob['time limit'], prob['memory limit'])
			os.chdir('..')
		else:
			if os.path.exists(os.path.join('tmp', prob['name'] + str(i) + '.out')):
				shutil.copy(os.path.join('tmp', prob['name'] + str(i) + '.out'), os.path.join('tmp', prob['name'] + '.out'))
				ret = None
				time = 0.0
			else:
				ret = 'Output file does not exist.'
				time = 0.0
		if not ret:
			if not os.path.exists(os.path.join('tmp', prob['name'] + '.out')):
				ret = 'Output file does not exist.'
				time = 0.0
				score = 0.0
			elif os.path.exists(os.path.join('data', prob['name'] + '_e')):
				shutil.copy(os.path.join('data', prob['name'] + '_e'), os.path.join('tmp', 'chk' + elf_suffix))
				os.system('%s %s %s %s' % (
					os.path.join('tmp', 'chk' + elf_suffix),
					os.path.join(path, prob['name'] + str(i) + '.in'),
					os.path.join('tmp', prob['name'] + '.out'),
					os.path.join(path, prob['name'] + str(i) + '.ans')
				))
				f = open(('/' if system != 'Windows' else '') + 'tmp/_eval.score')
				report = f.readline().strip()
				score = float(f.readline()) * 0.1
				f.close()
			else:
				ret = os.system('%s %s %s > log' % (
					diff_tool,
					os.path.join(path, prob['name'] + str(i) + '.ans'),
					os.path.join('tmp', prob['name'] + '.out')
				))
				if ret == 0:
					score = 1.0
					report = 'ok'
				else:
					score = 0.0
					report = 'wa'
		else:
			score = 0.0
			report = ret
		while os.path.exists(os.path.join('tmp', prob['name'] + '.out')):
			try:
				os.remove(os.path.join('tmp', prob['name'] + '.out'))
			except:
				pass
		if score == 0.0:
			time = 0.0
		# TODO: different scores for different cases
		scores.append(score / prob['test cases'] * 100)
		times.append(time)
		reports.append(report)
	return scores, times, reports
	
def test_one_day(probs, day_name):
	if not os.path.exists('result'):
		os.makedirs('result')
	for prob in probs:
		if day_name + '/' + prob['name'] not in prob_set:
			continue
		with open(os.path.join('result', prob['name'] + '.csv'), 'w') as fres:
			fres.write('%s,%s,summary,sample\n' % (prob['name'], ','.join(map(str, range(1, prob['test cases'] + 1)))))
			for user in os.listdir(prob['name']):
				if not problem_skip.match(user) and os.path.isdir(os.path.join(prob['name'], user)):
					for algo in os.listdir(os.path.join(prob['name'], user)):
						if not user_skip.match(algo) and os.path.isdir(os.path.join(prob['name'], user, algo)):
							if os.path.exists('tmp'):
								shutil.rmtree('tmp')
							shutil.copytree(os.path.join(prob['name'], user, algo), 'tmp')
							print('Now testing %s:%s:%s' % (prob['name'], user, algo))
							scores, times, reports = test(prob)
							while os.path.exists('tmp'):
								try:
									shutil.rmtree('tmp')
								except:
									pass
							tc = prob['test cases']
							scores = scores[:tc] + [sum(scores[:tc])] + scores[tc:]
							times = times[:tc] + [sum(times[:tc])] + times[tc:]
							reports = reports[:tc] + [''] + reports[tc:]
							'''fres.write('%s:,' % user)
							for i in range(prob['test cases']):
								fres.write('%.1f,%.3f,' % (scores[i], times[i]))
							fres.write('\n')
							fres.write('%s:,%s\n' % (algo, ',,'.join(reports)))'''
							scores = map(lambda i : '%.1f' % i, scores)
							times = map(lambda i : '%.3f' % i, times)
							for title, line in [(user, scores), (algo, times), ('', reports)]:
								fres.write('%s,%s\n' % (title, ','.join(line)))
	
def test_progs():
	for day_name, day_data in probs.items():
		if day_name not in day_set:
			continue
		os.chdir(day_name)
		test_one_day(day_data, day_name)
		os.chdir('..')
	
def deal_argv():
	global do_copy_files, do_test_progs, do_release, no_compiling, day_set, prob_set, probs
	do_copy_files = True
	do_test_progs = True
	do_release = True
	no_compiling = False
	day_set = None
	prob_set = None
	l = len(sys.argv)
	i = 1
	while i < l:
		if sys.argv[i] == '-i':
			i += 1
			os.chdir(sys.argv[i])
		elif sys.argv[i] == '-t':
			do_copy_files = False
			do_test_progs = True
			do_release = False
			no_compiling = False
		elif sys.argv[i] == '-f':
			do_copy_files = True
			do_test_progs = False
			do_release = False
			no_compiling = False
		elif sys.argv[i] == '-n':
			do_copy_files = True
			do_test_progs = False
			do_release = False
			no_compiling = True
		elif sys.argv[i] == '-r':
			do_copy_files = True
			do_test_progs = False
			do_release = True
			no_compiling = True
		elif sys.argv[i] == '-d':
			i += 1
			day_set = set(sys.argv[i].split(','))
		elif sys.argv[i] == '-p':
			i += 1
			prob_set = set(sys.argv[i].split(','))
		else:
			print('Options:')
			print('\t-i PATH: Specify a path to work. Otherwise, use current path.')
			print('\t-t: Only do test.')
			print('\t-f: Only copy and check data.')
			print('\t-n: Only copy and check data with source files like chk copied without compiling.')
			print('\t-r: Only copy, check data and release to a zip.')
			print('\t-d day0,day2: Only do those work for day0 and day2.')
			print('\t-p day0/sleep,day2/nodes: Only do those work for day0/sleep and day2/nodes.')
			print('Do not use -t and -f together. Do not use -d and -p together.')
			return False
		i += 1
	probs = json.load(open('probs.json'))
	if not day_set:
		day_set = set(probs.keys())
	if not prob_set:
		prob_set = set()
		for day, info in probs.items():
			for prob in info:
				prob_set.add(day + '/' + prob['name'])
	return True
	
def zip_tree(z, path):
	for name in os.listdir(path):
		#print(path)
		full_path = os.path.join(path, name)
		if os.path.isdir(full_path):
			zip_tree(z, full_path)
		else:
			z.write(full_path)
	
def release():
	print('make zip files.')
	for day_name, day_data in probs.items():
		if day_name not in day_set:
			continue
		with zipfile.ZipFile(day_name + '.zip', 'w') as z:
			os.chdir(day_name)
			zip_tree(z, 'data')
			zip_tree(z, 'down')
			zip_tree(z, 'discussion')
			try:
				z.write('description.pdf')
			except:
				warning('Can\'t find `description.pdf`.')
			os.chdir('..')
	
if __name__ == '__main__':
	if deal_argv():
		frep = open('tester.log', 'a')
		frep.write('Collection starts at %s.\n' % str(datetime.datetime.now()))
		if do_copy_files:
			copy_files()
		if do_test_progs:
			test_progs()
		if do_release:
			release()
		frep.close()
