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
from . import num2chinese
import platform
from . import base
from .base import log, pjoin

def find_all_data(kind, folder, key, conf = None):
	if not conf:
		conf = base.conf
	def find_data(path = ''):
		full_path = pjoin(prob.path, folder, path)
		for f in os.listdir(full_path):
			if os.path.isfile(pjoin(full_path, f)):
				if not f.endswith('.in'):
					continue
				fans = pjoin(full_path, f[:-3]) + '.ans'
				if not os.path.exists(fans) or not os.path.isfile(fans):
					continue
				name = base.rjoin(path, f[:-3])
				if name not in new_data and name not in exist_data:
					new_data.add(name)
			else:
				find_data(base.rjoin(path, f))
	def parse(data):
		tmp = base.sorter()(map(str, list(data)))
		ret = []
		for i in tmp:
			try:
				ret.append(int(i))
			except Exception as e:
				ret.append(i)
		return ret
	for prob in conf.probs(no_repeat = True):
		log.info(u'在题目`%s`下搜索%s数据。' % (prob.route, key))
		is_lfs = os.path.exists(pjoin(prob.path, '.gitattributes'))
		new_data = set()
		exist_data = set(map(str, prob.__getattribute__(key)))
		try:
			find_data()
		except Exception as e:
			log.warning(e)
		new_data = parse(new_data)
		for datum in new_data:
			log.info(u'发现新数据`%s`。' % (pjoin(prob.path, folder, str(datum))))
		if not is_lfs:
			for tdata in (exist_data, new_data):
				for datum in tdata:
					for suf in ('.in', '.out', '.ans'):
						fname = pjoin(prob.path, folder, str(datum) + suf)
						if os.path.exists(fname) and os.path.getsize(fname) >= 1024 * 1024:
							log.warning(u'题目`%s`下%s数据达到了1MiB，建议在该题下使用`python tuack.gen lfs`。' % (prob.route, key))
							break
					else:
						continue
					break
				else:
					continue
				break
		prob.__getattribute__(key).__iadd__(new_data)
		if kind not in prob:
			prob[kind] = []
		if len(new_data) > 0:
			prob[kind].append({'cases' : new_data})
		base.save_json(prob)
	
def find_all_code():
	def find_code(user, path):
		full_path = pjoin(prob.path, user, path)
		for f in os.listdir(full_path):
			if base.user_skip.match(f):
				continue
			if os.path.isfile(pjoin(full_path, f)):
				for key in base.compilers:
					if not f.endswith('.' + key):
						continue
					code_path = base.rjoin(user, path, f).replace('//', '/')
					if code_path not in exist_code:
						prob['users'][user][base.rjoin(path, f).replace('//', '/')] = {
							'path' : code_path,
							'expected' : '== 100' if 'std' in code_path or prob['name'] in code_path else []
						}
						log.info(u'发现新源代码`%s`。' % code_path)
					break
			else:
				find_code(user, base.rjoin(path, f))

	for prob in base.probs(no_repeat = True):
		if prob['type'] == 'output':
			log.info(u'题目`%s`是提交答案题，跳过。' % prob.route)
			continue
		log.info(u'在题目`%s`下搜索源代码。' % prob.route)
		if 'users' not in prob:
			prob['users'] = {}
		exist_code = set()
		for user, algos in prob['users'].items():
			for algo, path in algos.items():
				exist_code.add((path['path'] if type(path) == dict else path).replace('//', '/'))
		for f in os.listdir(prob.path):
			if base.user_skip.match(f) or os.path.isfile(pjoin(prob.path, f)):
				continue
			if f not in prob['users']:
				prob['users'][f] = {}
			find_code(f, '')
			if len(prob['users'][f]) == 0:
				prob['users'].pop(f)
		base.save_json(prob)

def sample_copy(src, tgt = None, path = ''):
	if not tgt:
		tgt = src
	full_tgt = pjoin(path, tgt)
	if os.path.exists(full_tgt) and not os.path.isfile(full_tgt):
		full_tgt = pjoin(full_tgt, src)
	if not os.path.exists(full_tgt):
		log.info(u'生成文件`%s`' % full_tgt)
		base.copy(
			pjoin(base.path, 'sample'),
			src,
			full_tgt
		)

def new_dir(folder, args = None):
	if not args:
		args = base.args
	if len(args) == 0:
		dirs = ['.']
	else:
		if not base.conf:
			log.error(u'当前文件夹下没有找到合法的`conf.json`文件。')
			log.info(u'尝试使用`python -m tuack.gen -h`获取如何生成一个工程。')
			return
		if folder == 'contest':
			log.error(u'文件夹层次错误：比赛工程不能放在其他工程中。')
			return
		if folder == 'day' and base.conf.folder != 'contest':
			log.error(u'文件夹层次错误：比赛日工程只能放在比赛工程中。')
			return
		if folder == 'problem' and base.conf.folder != 'day':
			log.error(u'文件夹层次错误：题目工程只能放在比赛日工程中。')
			return
		dirs = args
	for path in dirs:
		if not os.path.exists(path):
			os.makedirs(path)
		if path != '.' and path in base.conf['subdir']:
			log.warning(u'`%s`已经在工程中了，跳过它的建立。' % path)
			log.info(u'如果需要强制建立，需要将其从`conf.yaml`中移除。')
			continue
		copy = lambda src, tgt = None: sample_copy(src, tgt, path)
		def copy_conf(inp):
			if base.dump_format != 'json':
				open(pjoin(path, 'conf.' + base.dump_format), 'wb').write(
					base.dump_formats[base.dump_format](
						json.loads(open(pjoin(base.path, 'sample', inp), 'rb').read().decode('utf-8'))
					)
				)
			else:
				copy(inp, 'conf.json')
		copy(folder + '.gitignore', '.gitignore')
		copy_conf(folder + '.json')
		if folder == 'problem':
			if base.git_lfs:
				copy(folder + '.gitattributes', '.gitattributes')
			else:
				log.info(u'现在不默认用git-lfs，如需，用`python -m tuack.gen lfs`添加。')
			for ff in ('data', 'down', 'pre', 'statement', 'tables', 'resources', 'solution'):
				st_path = pjoin(path, ff)
				if not os.path.exists(st_path):
					os.makedirs(st_path)
				for f in os.listdir(pjoin(base.path, 'sample', ff)):
					copy(pjoin(ff, f), pjoin(ff, f))
		if path != '.':
			conf = base.load_json(path)
			conf['name'] = path
			conf.path = path
			if path == 'day0':
				conf['title']['zh-cn'] = u'试机'
			elif path[:3] == 'day':
				try:
					num = int(path[3:])
					conf['title']['zh-cn'] = u'第' + num2chinese.num2chinese(num) + u'试'
				except Exception as e:
					pass
			base.save_json(conf)
	if len(args) != 0:
		for arg in args:
			if arg not in base.conf['subdir']:
				base.conf['subdir'].append(arg)
		base.save_json(base.conf)

def upgrade():
	if base.conf:	#是conf.json格式的老版本
		used = {}
		def upgrade_r(conf):
			'''
			非最新版本return False
			'''
			def upgrade_None(conf):
				log.info(u'将`%s`从None版本升级到0版本。' % conf.route)
				conf['version'] = 0
				if conf.folder == 'problem':
					for folder, cases, key in [('data', 'test cases', 'data'), ('down', 'sample count', 'samples')]:
						if cases in conf:
							cnt = conf.pop(cases)
							for i in range(1, cnt + 1):
								for suf in ['.in', '.ans']:
									try:
										ff = pjoin(conf.path, folder, conf['name'] + str(i) + suf)
										ft = pjoin(conf.path, folder, str(i) + suf)
										os.rename(ff, ft)
									except FileNotFoundError as e:
										if os.path.exists(ft):
											log.info('`%s`已经改名，跳过重命名。' % ft)
										else:
											log.error('`%s`和`%s`都找不到，可能你的文件命名错误。' % (ff, ft))
							work_list[key](conf)
				return False
			def upgrade_0(conf):
				log.info(u'将`%s`从0版本升级到1版本。' % conf.route)
				conf['version'] = 1
				if conf.folder == 'problem':
					if 'users' not in conf:
						conf['users'] = {}
					if 'pre' not in conf:
						conf['pre'] = []
					for user, algos in conf['users'].items():
						for algo in algos:
							if type(algos[algo]) == str:
								algos[algo] = {'path' : algos[algo], 'expected' : {}}
				return False
			def upgrade_1(conf):
				log.info(u'将`%s`从1版本升级到2版本。' % conf.route)
				conf['version'] = 2
				if conf.folder == 'problem':
					if 'users' not in conf:
						conf['users'] = {}
					if 'packed' in conf:
						conf.pop('packed')
					for user, algos in conf['users'].items():
						for algo, info in algos.items():
							if type(info.get('expected', None)) == dict:
								info['expected'] = ['%s %s' % (key, val) for key, val in info['expected'].items()]
								if len(info['expected']) == 1:
									info['expected'] = info['expected'][0]
				return False
			def upgrade_2(conf):
				log.info(u'`%s`是最新版本。' % conf.route)
				return True
			path = os.path.abspath(conf.path)
			if path in used:
				for key in used[path]:
					conf[key] = used[path][key]
			while not eval('upgrade_' + str(conf['version']))(conf):
				pass
			for sub in conf.sub:
				upgrade_r(sub)
			used[path] = conf
		upgrade_r(base.conf)
		base.save_json(base.conf)
	else:			#是prob(s).json格式的老版本
		if not os.path.exists('probs.json'):
			log.error(u'找不到`probs.json`。')
			return
		old_json = json.loads(open('probs.json', 'rb').read().decode('utf-8'))
		new_dir('contest', [])
		base.conf = base.load_json()
		base.conf.pop('version')
		new_dir('day', base.sorter()(old_json.keys()))
		base.conf = base.load_json()
		for day in base.conf.sub:
			day.pop('version')
			day['subdir'] += [prob for prob in old_json[day['name']]]
		base.save_json(base.conf)
		base.conf = base.load_json()
		upgrade()

def copy_lfs():
	for prob in base.probs(no_repeat = True):
		copy = lambda src, tgt = None: sample_copy(src, tgt, prob.path)
		copy('problem.gitattributes', '.gitattributes')

def copy_chk():
	if base.conf['folder'] != 'problem':
		log.error(u'答案校验器只能添加给题目工程，请到题目目录下运行。')
		return
	for prob in base.probs(no_repeat = True):
		copy = lambda src, tgt = None: sample_copy(src, tgt, prob.path)
		if not os.path.exists(pjoin(prob.path, 'data', 'chk')):
			os.makedirs(pjoin(prob.path, 'data', 'chk'))
		copy('chk.cpp', pjoin('data', 'chk'))

def copy_prec():
	if base.conf['folder'] != 'contest':
		log.error(u'考生须知只能添加给比赛工程。')
		return
	path = '.'
	copy = lambda src, tgt = None: sample_copy(src, tgt, path)
	for ff in ('precautions', ):
		st_path = pjoin(path, ff)
		if not os.path.exists(st_path):
			os.makedirs(st_path)
		for f in os.listdir(pjoin(base.path, 'sample', ff)):
			copy(pjoin(ff, f), pjoin(ff, f))

work_list = {
	'data' : lambda conf = None: find_all_data('data', 'data', 'test_cases', conf),
	'samples' : lambda conf = None: find_all_data('samples', 'down', 'sample_cases', conf),
	'pre' : lambda conf = None: find_all_data('pre', 'pre', 'pre_cases', conf),
	'code' : find_all_code,
	'contest' : lambda : new_dir('contest'),
	'day' : lambda : new_dir('day'),
	'problem' : lambda : new_dir('problem'),
	'upgrade' : upgrade,
	'lfs' : copy_lfs,
	'chk' : copy_chk,
	'prec' : copy_prec
}
work_list['auto'] = lambda : [work_list[key]() for key in ['data', 'samples', 'pre', 'code']]
work_list['n'] = work_list['contest']
work_list['d'] = work_list['day']
work_list['p'] = work_list['problem']
work_list['t'] = work_list['data']
work_list['s'] = work_list['samples']
work_list['u'] = work_list['upgrade']
work_list['a'] = work_list['auto']

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
		log.info(u'这个工具用于快速建立一道题目。')
		log.info(u'支持的工作：')
		log.info(u'  contest  在当前目录下生成一场比赛，不支持参数。')
		log.info(u'  n        同contest。')
		log.info(u'  day      无参数表示在当前目录下生成一个比赛日，比赛日可以是独立的工程；')
		log.info(u'           有参数表示在当前比赛下依次生成名叫参数1，参数2，…的比赛日，')
		log.info(u'           有参数必须保证当前目录是比赛。')
		log.info(u'  d        同day。')
		log.info(u'  problem  无参数表示在当前目录下生成一道题目，题目可以是独立的工程；')
		log.info(u'           有参数表示在当前比赛日下依次生成名叫参数1，参数2，…的题目，')
		log.info(u'           有参数必须保证当前目录是比赛日。')
		log.info(u'  p        同problem。')
		log.info(u'  data     在题目工程的data文件夹中搜索数据并添加到配置文件。')
		log.info(u'           对于比赛工程和比赛日工程，此操作将应用于所有子题目工程，下同。')
		log.info(u'  t        同data。')
		log.info(u'  samples  在题目工程的down文件夹中搜索样例并添加到配置文件。')
		log.info(u'  s        同samples。')
		log.info(u'  pre      在题目工程的pre文件夹中搜索预测试数据并添加到配置文件。')
		log.info(u'  code     在题目工程的非数据文件夹中搜索源代码并添加到配置文件。')
		log.info(u'  c        同code。')
		log.info(u'  auto     等于一次性做了上述4件事情。')
		log.info(u'  a        同auto。')
		log.info(u'  lfs      用git-lfs维护所有的*.in/out/ans，当数据较大时使用。')
		log.info(u'  chk      添加一个空的答案校验器或称spj，建议在此基础上修改以兼容。')
		log.info(u'  prec     对于比赛工程，添加考生须知文件。')
		log.info(u'  upgrade  升级老版本工程到现在版本的工程。')
		log.info(u'  u        同upgrade。')
