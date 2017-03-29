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
from common import *
import common
	
def run_windows(name, tl, ml, input = None, output = None):
	'''
	On windows, memory limit is not considered.
	'''
	t = time.clock()
	try:
		fin = (open(input) if input else None)
		fout = (open(output, 'w') if output else None)
		pro = subprocess.Popen(name, stdin = fin, stdout = fout)
		if fout:
			fout.close()
		if fin:
			fin.close()
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

def runner_linux(name, que, ml, input = None, output = None):
	pro = subprocess.Popen(
		'ulimit -v %d; time -f "%%U" -o timer ./%s %s %s' % (
			common.memory2bytes(ml) // 1024,
			name,
			'< %s' % input if input else '',
			'> %s' % output if output else '',
		),
		shell = True,
		preexec_fn = os.setsid
	)
	que.put(pro.pid)
	ret = pro.wait()
	que.put(ret)
	
def run_linux(name, tl, ml, input = None, output = None):
	que = Queue()
	pro = Process(target = runner_linux, args = (name, que, ml, input, output))
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
			ret, time = run(prob['name'], prob['time limit'], prob['memory limit'], prob['name'] + '.in', prob['name'] + '.out')
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
	for prob in probs:
		if day_name + '/' + prob['name'] not in common.prob_set:
			continue
		not_empty = False
		with open(os.path.join('..', 'result', day_name, prob['name'] + '.csv'), 'w') as fres:
			fres.write('%s,%s,summary,sample\n' % (prob['name'], ','.join(map(str, range(1, prob['test cases'] + 1)))))
			for user in os.listdir(prob['name']):
				if not problem_skip.match(user) and os.path.isdir(os.path.join(prob['name'], user)) and (not common.user_set or day_name + '/' + prob['name'] + '/' + user in common.user_set):
					for algo in os.listdir(os.path.join(prob['name'], user)):
						if not user_skip.match(algo) and os.path.isdir(os.path.join(prob['name'], user, algo)) and (not common.algo_set or day_name + '/' + prob['name'] + '/' + user + '/' + algo in common.algo_set):
							not_empty = True
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
							scores = map(lambda i : '%.1f' % i, scores)
							times = map(lambda i : '%.3f' % i, times)
							for title, line in [(user, scores), (algo, times), ('', reports)]:
								fres.write('%s,%s\n' % (title, ','.join(line)))
		if common.start_file and not_empty:
			if common.system == 'Windows':
				os.startfile(os.path.join('..', 'result', day_name, prob['name'] + '.csv'))
			else:
				subprocess.call(["xdg-open", os.path.join('..', 'result', day_name, prob['name'] + '.csv')])
	
def test_progs():
	if not os.path.exists('result'):
		os.makedirs('result')
	for day_name, day_data in common.probs.items():
		if day_name not in common.day_set:
			continue
		if not os.path.exists(os.path.join('result', day_name)):
			os.makedirs(os.path.join('result', day_name))
		os.chdir(day_name)
		test_one_day(day_data, day_name)
		os.chdir('..')
	
if __name__ == '__main__':
	if deal_argv():
		common.work = 'test'
		infom('Testing starts at %s.\n' % str(datetime.datetime.now()))
		test_progs()
