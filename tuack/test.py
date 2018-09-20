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

def time2float(inp):
	m = re.match(r'(\d*)(:|h)(\d*)(:|m)(\d*\.?\d*)s?', inp)
	if m:
		return float(m.group(1)) * 3600 + float(m.group(3)) * 60 + float(m.group(5))
	m = re.match(r'(\d*)(:|m)(\d*\.?\d*)s?', inp)
	if m:
		return float(m.group(1)) * 60 + float(m.group(3))
	m = re.match(r'(\d*\.?\d*)s?', inp)
	if m:
		return float(m.group(1))
	raise Exception('Timer broken')

def run_windows(name, tl, ml, input = None, output = None, vm = None):
	'''
	On windows, memory limit is not considered.
	'''
	try:
		fin = (open(input) if input else None)
		fout = (open(output, 'w') if output else None)
		t = time.clock()
		pro = subprocess.Popen(vm(name, ml) if vm else name, stdin = fin, stdout = fout)
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
		if (time.clock() - t) >= tl * base.time_multiplier:
			pro.kill()
			t = 0.0
			ret = 'Time out.'
			break
		time.sleep(1e-2)
	time.sleep(1e-2)
	return ret, t

def runner_linux(name, que, ml, input = None, output = None, vm = None):
	pro = subprocess.Popen(
		'%s time -f "%%%s" -o timer %s %s %s' % (
			'ulimit -v %d;' % int(base.Memory(ml).KB) if vm != base.runners['java'] else '',
			'U' if base.user_time else 'E',
			vm(name, ml) if vm else './%s' % name,
			'< %s' % input if input else '',
			'> %s' % output if output else '',
		),
		shell = True,
		preexec_fn = os.setsid
	)
	que.put(pro.pid)
	ret = pro.wait()
	que.put(ret)
	
def run_linux(name, tl, ml, input = None, output = None, vm = None):
	que = Queue()
	pro = Process(target = runner_linux, args = (name, que, ml, input, output, vm))
	pro.start()
	pro.join(tl * base.time_multiplier)
	if que.qsize() == 0:
		log.error('Runner broken.')
	elif que.qsize() == 1:
		ret = 'Time out.'
		pid = que.get()
		os.killpg(os.getpgid(pid), signal.SIGTERM)
		t = 0.
	else:
		pid = que.get()
		ret = que.get()
		if ret == 0:
			try:
				t = time2float(open('timer').readline())
			except Exception as e:
				log.debug(e)
				log.warning('Timer broken.')
				t = 0.
			ret = None
		else:
			ret = 'Runtime error %d.(MLE will cause RE as well in linux)' % ret
			t = 0.
	return ret, t

def runner_mac(name, que, ml, input = None, output = None, vm = None):
	pro = subprocess.Popen(
		'ulimit -v %d; (time -p %s %s %s) 2> timer' % (
			int(base.Memory(ml).KB),
			vm(name, ml) if vm else './%s' % name,
			'< %s' % input if input else '',
			'> %s' % output if output else '',
		),
		shell = True,
		preexec_fn = os.setsid
	)
	que.put(pro.pid)
	ret = pro.wait()
	que.put(ret)

def run_mac(name, tl, ml, input = None, output = None, vm = None):
	que = Queue()
	pro = Process(target = runner_mac, args = (name, que, ml, input, output, vm))
	pro.start()
	pro.join(tl * base.time_multiplier)
	if que.empty():
		log.error('Runner broken.')
	else:
		pid = que.get()
		if que.empty():
			ret = 'Time out.'
			os.killpg(os.getpgid(pid), signal.SIGTERM)
			t = 0.
		else:
			ret = que.get()
			if ret == 0:
				try:
					with open('timer') as f:
						for i in range(2 if base.user_time else 1):
							line = f.readline()
						t = time2float(line.strip().split()[-1])
				except:
					base.warning('Timer broken.')
					t = 0.
				ret = None
			else:
				ret = 'Runtime error %d.' % ret
				t = 0.
	return ret, t

if base.system == 'Linux':
	run = run_linux
elif base.system == 'Windows':
	run = run_windows
elif base.system == 'Darwin':
	run = run_mac
else:
	run = run_linux
	log.warning(u'未知的操作系统，尝试当做Linux运行。')
	
def compile(prob, name):
	for lang, args in prob['compile'].items():
		if os.path.exists(pjoin('tmp', name + '.' + lang)):
			base.check_install(lang)
			os.chdir('tmp')
			try:
				ret = subprocess.call(
					base.compilers[lang](name, args, base.macros[base.work], ml = prob['memory limit']),
					shell = True,
					stdout = open('stdout', 'w'),
					stderr = open('stderr', 'w')
				)
			except Exception as e:
				with open('stderr', 'a') as f:
					f.write(str(e))
				ret = -1
			os.chdir('..')
			if ret:
				log.info('`' + name + '.' + lang + u'`编译失败，详情见`compile.log`。')
				with open('compile.log', 'a') as f:
					import __main__
					f.write(u'## 脚本%s/，工程路径%s，参数%s，开始于%s。\n' % (__main__.__file__, os.getcwd(), str(sys.argv[1:]), str(datetime.datetime.now())))
					f.write(u'## 测试题目`%s`，编译失败代码名称`%s.%s`\n' % (prob['name'], name, lang))
					try:
						f.write(u'编译器输出的stdout为：\n')
						f.write(open('tmp/stdout').read())
					except Exception as e:
						f.write(u'编译器没有输出stdout，具体错误为：\n')
						f.write(str(e) + '\n')
					try:
						f.write(u'编译器输出的stderr为：\n')
						f.write(open('tmp/stderr').read())
					except Exception as e:
						f.write(u'编译器没有输出stderr，具体错误为：\n')
						f.write(str(e) + '\n')
				raise Exception('`' + name + '.' + lang + '` compile failed.')
			return lang
	else:
		raise Exception('Can\'t find source file.')

def test(prob, name):
	scores = []
	times = []
	reports = []
	if prob['type'] == 'program':
		try:
			lang = compile(prob, name)
		except Exception as e:
			for i in range(len(prob.test_cases) + len(prob.sample_cases)):
				scores.append(0.0)
				times.append(0.0)
				reports.append(str(e))
			return scores, times, reports
	all_cases = prob.test_cases + prob.sample_cases + prob.pre_cases
	for case in all_cases:
		print('Case %s:%s  ' % (case['key'], case), end = '\r')
		sys.stdout.flush()
		shutil.copy(case.full() + '.in', pjoin('tmp', 'in'))
		shutil.copy(case.full() + '.ans', pjoin('tmp', 'ans'))
		for fname in ('in', 'ans'):
			if base.system == 'Windows':
				base.unix2dos(pjoin('tmp', fname))
			else:
				base.dos2unix(pjoin('tmp', fname))
		if prob['type'] == 'program':
			os.chdir('tmp')
			ret, time = run(name, prob['time limit'], prob['memory limit'], 'in', 'out', base.runners[lang])
			os.chdir('..')
		elif prob['type'] == 'output':
			if os.path.exists(pjoin('tmp', case['case'] + '.out')):
				shutil.copy(pjoin('tmp', case['case'] + '.out'), pjoin('tmp', 'out'))
				ret = None
				time = 0.0
			else:
				ret = 'Output file does not exist.'
				time = 0.0
		else:
			log.error(u'错误的题目类型`%s`。' % prob['type'])
			raise Exception('problem type error.')
		if not ret:
			if not os.path.exists(pjoin('tmp', 'out')):
				ret = 'Output file does not exist.'
				time = 0.0
				score = 0.0
			elif prob.chk:
				shutil.copy(pjoin('bin', prob.route), pjoin('tmp', 'chk' + base.elf_suffix))
				open('100.0', 'w').write('100.0\n')
				os.system('%s %s %s %s 100.0 tmp/score tmp/info' % (
					pjoin('tmp', 'chk' + base.elf_suffix),
					pjoin('tmp', 'in'),
					pjoin('tmp', 'out'),
					pjoin('tmp', 'ans')
				))
				os.remove('100.0')
				try:
					arbiter_out = ('/' if base.system != 'Windows' else '') + 'tmp/_eval.score'
					f = open(arbiter_out)
					report = f.readline().strip()
					score = float(f.readline()) * 0.1
					f.close()
					shutil.remove(arbiter_out)
				except Exception as e:
					try:
						report = open('tmp/info').read().strip()
					except Exception as e:
						report = ''
					score = float(open('tmp/score').readline()) * .01
			else:
				ret = os.system('%s %s %s > log' % (
					base.diff_tool,
					pjoin('tmp', 'ans'),
					pjoin('tmp', 'out')
				))
				if ret == 0:
					score = 1.0
					report = 'ok'
					if prob['type'] != 'output' and time > prob['time limit']:
						score = 0.0
						report += '(but time out)'
				else:
					score = 0.0
					report = 'wa'
					if prob['type'] != 'output' and time > prob['time limit']:
						report += '(and time out)'
		else:
			score = 0.0
			report = ret
		while os.path.exists(pjoin('tmp', prob['name'] + '.out')):
			try:
				os.remove(pjoin('tmp', prob['name'] + '.out'))
			except:
				pass
		scores.append(score)
		times.append(time)
		reports.append(report)
	return scores, times, reports

def packed_score(scores, times, reports, score_map, prob):
	pscore = []
	ptime = []
	preport = []
	for datum in prob.data:
		pscore.append(datum.score * min((scores[score_map[i]] for i in datum['cases'])))
		ptime.append(sum((times[score_map[i]] for i in datum['cases'] if scores[score_map[i]] > 0)))
		preport.append('Total %.1f' % datum.score)
	pscore.append(sum(pscore))
	ptime.append(sum(ptime))
	preport.append('')
	return (pscore, ptime, preport)
	
def test_problem(prob):
	log.info(u'尝试评测题目`%s`。' % prob.route)
	if 'users' not in prob:
		log.warning(u'题目`%s`缺少`users`字段，没有找到出题人的程序。' % prob.route)
		log.info(u'你需要在工程中放置你的代码，然后使用`python -m tuack.gen code`搜索源代码，或直接配置`users`字段。')
		return
	if 'data' not in prob or len(prob.test_cases) == 0:
		log.warning(u'题目`%s`缺少`data`字段，找不到测试数据。' % prob.route)
		log.info(u'你需要在文件夹`%s`下按*.in和*.ans格式存放测试数据，' % pjoin(prob.path, 'data'))
		log.info(u'然后使用`python -m tuack.gen data`添加它们或直接配置`data`字段。')
	if 'samples' not in prob or len(prob.sample_cases) == 0:
		log.warning(u'题目`%s`缺少`samples`字段，找不到样例数据。' % prob.route)
		log.info(u'你需要在文件夹`%s`下按*.in和*.ans格式存放样例数据，' % pjoin(prob.path, 'down'))
		log.info(u'然后使用`python -m tuack.gen samples`添加它们或直接配置`samples`字段。')
	if 'pre' in prob and len(prob.pre_cases) == 0:
		log.warning(u'题目`%s`的`pre`字段为空，找不到预测试数据。' % prob.route)
		log.info(u'如果这道题目有预测试数据，你需要在文件夹`%s`下按*.in和*.ans格式存放预测试数据，' % pjoin(prob.path, 'pre'))
		log.info(u'然后使用`python -m tuack.gen pre`在文件夹`%s`下搜索预测试数据。' % (pjoin(prob.path, 'pre')))
		log.info(u'如果这道题目没有预测试数据，你需要删除`conf.*`中的`pre`字段。')
	if len(prob.data) == 1 and prob.data[0].get('score') != 100:
		log.warning(u'题目`%s`的`data`字段只有一个元素，可能没有正确配置数据。' % prob.route)
		log.info(u'如果是一个包的CPC赛制，需要在这个元素中配置`score`项为100。')
		log.info(u'如果是多点或多子任务的赛制，需要将每类数据分类配置或打包配置。')
		log.info(u'详情请见%s。' % base.wiki(u'配置题目#数据'))
	log.info(u'共%d组样例，%d个预测试点，%d个测试点，%s打包评测%s。' % (
		len(prob.sample_cases),
		len(prob.pre_cases),
		len(prob.test_cases),
		u'是' if prob.packed else u'不是',
		(u'（共%d个包）' % len(prob.data) if len(prob.data) != 1 else u'（看样子是一个包的CPC赛制）') if prob.packed else ''
	))

	prob_failed = False

	case_features = [[] for i in range(len(prob.data))]

	with open(pjoin('result', prob.route) + '.csv', 'w') as fres:
		fres.write('%s,%s%s,summary,sample%s,pre%s\n' % (
			prob['name'],
			','.join(prob.test_cases),
			',' + ','.join(map(lambda datum : '{' + ';'.join(map(str, datum['cases'])) + '}', prob.data)) \
				if prob.packed else '',
			','.join(prob.sample_cases),
			','.join(prob.pre_cases)
		))
		for user, algos in prob.users().items():
			if not prob.all:
				match = base.any_prefix(rjoin(prob.route, user))
				if not match:
					continue
			for algo, algo_obj in algos.items():
				path = algo_obj['path']
				expe = algo_obj.get('expected')
				if not expe or len(expe) == 0:
					log.warning(u'程序`%s/%s`没有设置期望得分。' % (user, algo))
					log.info(u'如果该程序是标程、部分分程序或骗分程序等，需要设置它的`expected`字段。')
					log.info(u'有多种设置的格式，例如：`== 60`表示该程序应该得到60分。')
					log.info(u'如果该程序是其他功能程序，例如数据生成器，请将该程序从配置文件中移除。')
				if (not prob.all and match != 1 and not base.any_prefix(rjoin(prob.route, user, algo))):
					continue
				while os.path.exists('tmp'):
					try:
						shutil.rmtree('tmp')
					except:
						time.sleep(1e-2)
				if prob['type'] == 'program':
					while True:
						try:
							os.makedirs('tmp')
						except:
							time.sleep(1e-2)
						else:
							break
					try:
						shutil.copy(path, pjoin('tmp', path.split('/')[-1]))
					except Exception as e:
						log.error(u'程序`%s`没有找到。' % path)
						log.info(e)
						log.info(u'如果该程序是测试程序，请确保该程序存在；如果不是，请将其从`conf.*`中移除。')
						continue
				elif prob['type'] == 'output':
					for i in range(20):
						try:
							shutil.copytree(path, 'tmp')
						except Exception as e:
							time.sleep(1e-2)
							log.error(u'测试输出文件包`%s`没有找到或复制失败，正在重试 %d / 20。' % (path, i + 1))
							log.info(e)
						else:
							break
					else:
						log.error(u'跳过该输出文件包。')
						log.info(u'如果该文件包是测试输出，请确保该文件包存在；如果不是，请将其从`conf.*`中移除。')
				log.info(u'测试程序 %s:%s:%s' % (prob['name'], user, algo))
				scores, times, reports = test(prob, path.split('/')[-1].split('.')[0])
				while os.path.exists('tmp'):
					try:
						shutil.rmtree('tmp')
					except:
						pass
				tc = len(prob.test_cases)
				score_map = {}
				for i in range(tc):
					score_map[prob.test_cases[i]] = i
				if prob.packed:
					packed = packed_score(scores[:tc], times[:tc], reports[:tc], score_map, prob)
					tot = sum(packed[0][:-1])
					scores = scores[:tc] + packed[0] + scores[tc:]
					times = times[:tc] + packed[1] + times[tc:]
					reports = reports[:tc] + packed[2] + reports[tc:]
					for i, s in enumerate(packed[0][:-1]):
						case_features[i].append(s)
				elif tc > 0:
					ratio = 100. / tc
					scores = [score * ratio for score in scores[:tc] + [sum(scores[:tc])] + scores[tc:]]
					packed = packed_score(scores[:tc], times[:tc], reports[:tc], score_map, prob)
					tot = sum(scores[:tc])
					times = times[:tc] + [sum((val for idx, val in enumerate(times[:tc]) if scores[idx] > 0))] + times[tc:]
					reports = reports[:tc] + [''] + reports[tc:]
					for i, s in enumerate(packed[0][:-1]):
						case_features[i].append(s)
				else:
					# FIXME: Do I do this?
					tot = sum(scores)
					scores = [0.0, 0.0] + scores
					times = [0.0, 0.0] + times
					reports = ['', ''] + reports

				if not prob.expect(user, algo, tot):
					log.error(u'未达到预期。预期分数 %s ，实际得分 %.2f' % (algo_obj['expected'], tot))
					prob_failed = True

				scores = map(lambda i : '%.2f' % i, scores)
				times = map(lambda i : '%.3f' % i, times)
				reports = map(lambda i : i.replace('\n', '\\n').replace(',', ';').replace('\r', ''), reports)
				for title, line in [(user, scores), (algo, times), ('', reports)]:
					fres.write('%s,%s\n' % (title, ','.join(line)))
	used_features = {}
	for i, f in enumerate(case_features):
		tf = tuple(f)
		if tf in used_features:
			log.warning(u'没有程序区分数据包%s和%s。' % (prob.data[used_features[tf]]['cases'], prob.data[i]['cases']))
			log.info(u'对每种不同类型的数据，都应当有程序可以被这些数据区分。')
		else:
			used_features[tf] = i
	if base.start_file:
		base.xopen_file(pjoin('result', prob.route) + '.csv')
	return not prob_failed

def test_progs():
	test_failed = False
	if base.conf.folder != 'problem' and not os.path.exists('result'):
		os.makedirs('result')
	for day in base.days():
		path = pjoin('result', day.route)
		if not os.path.exists(path):
			os.makedirs(path)
	for prob in base.probs():
		try:
			if not test_problem(prob):
				test_failed = True
		except Exception as e:
			log.error(traceback.format_exc())
	return not test_failed

if __name__ == '__main__':
	try:
		if base.init():
			base.work = 'test'
			if base.do_pack:
				from . import packer
				base.run_exc(packer.test)
			ex, success = base.run_exc(test_progs)
			if ex or not success:
				sys.exit(1)
		else:
			log.info(u'这是测试出题人数据和程序的测试器，测试器没有细分的工作。')
			sys.exit(1)
	except base.NoFileException as e:
		log.error(e)
		log.info(u'尝试使用`python -m tuack.gen -h`获取如何生成一个工程。')
		sys.exit(1)
