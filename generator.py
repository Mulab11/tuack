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

def find_all_data(kind, folder, key, conf = None):
	if not conf:
		conf = common.conf
	def find_data(path = ''):
		full_path = common.pjoin(prob.path, folder, path)
		for f in os.listdir(full_path):
			if os.path.isfile(common.pjoin(full_path, f)):
				if not f.endswith('.in'):
					continue
				fans = common.pjoin(full_path, f[:-3]) + '.ans'
				if not os.path.exists(fans) or not os.path.isfile(fans):
					continue
				name = common.rjoin(path, f[:-3])
				if name not in new_data and name not in exist_data:
					new_data.add(name)
			else:
				find_data(common.rjoin(path, f))
	def parse(data):
		tmp = common.sorter()(map(str, list(data)))
		ret = []
		for i in tmp:
			try:
				ret.append(int(i))
			except Exception as e:
				ret.append(i)
		return ret
	for prob in conf.probs():
		log.info(u'在题目`%s`下搜索%s数据。' % (prob.route, key))
		new_data = set()
		exist_data = set(map(str, prob.__getattribute__(key)))
		try:
			find_data()
		except Exception as e:
			log.warning(e)
		new_data = parse(new_data)
		for datum in new_data:
			log.info(u'发现新数据`%s`。' % (common.pjoin(prob.path, folder, str(datum))))
		prob.__getattribute__(key).__iadd__(new_data)
		if kind not in prob:
			prob[kind] = []
		if len(new_data) > 0:
			prob[kind].append({'cases' : new_data})
		common.save_json(prob)
	
def find_all_code():
	def find_code(user, path):
		full_path = common.pjoin(prob.path, user, path)
		for f in os.listdir(full_path):
			if common.user_skip.match(f):
				continue
			if os.path.isfile(common.pjoin(full_path, f)):
				for key in common.compilers:
					if not f.endswith('.' + key):
						continue
					if common.rjoin(user, path, f) not in exist_code:
						prob['users'][user][common.rjoin(path, f)] = common.rjoin(user, path, f)
						log.info(u'发现新源代码`%s`。' % common.rjoin(user, path, f))
					break
			else:
				find_code(user, common.rjoin(path, f))

	for prob in common.probs():
		if prob['type'] == 'output':
			log.info(u'题目`%s`是提交答案题，跳过。' % prob.route)
			continue
		log.info(u'在题目`%s`下搜索源代码。' % prob.route)
		if 'users' not in prob:
			prob['users'] = {}
		exist_code = set()
		for user, algos in prob['users'].items():
			for algo, path in algos.items():
				exist_code.add(path)
		for f in os.listdir(prob.path):
			if common.user_skip.match(f) or os.path.isfile(common.pjoin(prob.path, f)):
				continue
			if f not in prob['users']:
				prob['users'][f] = {}
			find_code(f, '')
			if len(prob['users'][f]) == 0:
				prob['users'].pop(f)
		common.save_json(prob)

def new_dir(folder, args = None):
	def copy(src, tgt = None):
		if not tgt:
			tgt = src
		if not os.path.exists(common.pjoin(path, tgt)):
			common.copy(
				common.pjoin(common.path, 'sample'),
				src,
				common.pjoin(path, tgt)
			)

	if not args:
		args = common.args
	if len(args) == 0:
		dirs = ['.']
	else:
		if not common.conf:
			log.error(u'当前文件夹下没有找到合法的`conf.json`文件。')
			log.info(u'尝试使用`python -m generator -h`获取如何生成一个工程。')
			return
		dirs = args
	for path in dirs:
		if not os.path.exists(path):
			os.makedirs(path)
		copy(folder + '.gitignore', '.gitignore')
		copy(folder + '.json', 'conf.json')
		if folder == 'problem':
			copy(folder + '.gitattributes', '.gitattributes')
			for ff in ('data', 'down', 'statement'):
				st_path = common.pjoin(path, ff)
				if not os.path.exists(st_path):
					os.makedirs(st_path)
				for f in os.listdir(common.pjoin(common.path, 'sample', ff)):
					copy(common.pjoin(ff, f), common.pjoin(ff, f))
		if path != '.':
			conf = common.load_json(path)
			conf['name'] = path
			conf.path = path
			common.save_json(conf)
	if len(args) != 0:
		common.conf['subdir'] = sorted(list(set(common.conf['subdir'] + args)))
		common.save_json(common.conf)

def upgrade():
	if common.conf:	#是conf.json格式的老版本
		def upgrade_r(conf):
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
										ff = common.pjoin(conf.path, folder, conf['name'] + str(i) + suf)
										ft = common.pjoin(conf.path, folder, str(i) + suf)
										os.rename(ff, ft)
									except FileNotFoundError as e:
										if os.path.exists(ft):
											log.info('`%s`已经改名，跳过重命名。' % ft)
										else:
											log.error('`%s`和`%s`都找不到，可能你的文件命名错误。' % (ff, ft))
							work_list[key](conf)
			def upgrade_0(conf):
				log.info(u'`%s`是最新版本。' % conf.route)
			eval('upgrade_' + str(conf['version']))(conf)
			for sub in conf.sub:
				upgrade_r(sub)
		upgrade_r(common.conf)
		common.save_json(common.conf)
	else:			#是prob(s).json格式的老版本
		if not os.path.exists('probs.json'):
			log.error(u'找不到`probs.json`。')
			return
		old_json = json.loads(open('probs.json', 'rb').read().decode('utf-8'))
		new_dir('contest', [])
		common.conf = common.load_json()
		common.conf.pop('version')
		new_dir('day', common.sorter()(old_json.keys()))
		common.conf = common.load_json()
		for day in common.conf.sub:
			day.pop('version')
			day['subdir'] += [prob for prob in old_json[day['name']]]
		common.save_json(common.conf)
		common.conf = common.load_json()
		upgrade()

work_list = {
	'data' : lambda conf = None: find_all_data('data', 'data', 'test_cases', conf),
	'samples' : lambda conf = None: find_all_data('samples', 'down', 'sample_cases', conf),
	'code' : find_all_code,
	'contest' : lambda : new_dir('contest'),
	'day' : lambda : new_dir('day'),
	'problem' : lambda : new_dir('problem'),
	'upgrade' : upgrade
}

if __name__ == '__main__':
	try:
		result = common.init()
	except common.NoFileException as e:
		common.conf = None
		result = True
	if result:
		for common.work in common.works:
			common.run_exc(work_list[common.work])
	else:
		log.info(u'这个工具用于快速建立一道题目。')
		log.info(u'支持的工作：')
		log.info(u'  upgrade  升级老版本工程到现在版本的工程。')
		log.info(u'  contest  在当前目录下生成一场比赛，不支持参数。')
		log.info(u'  day      无参数表示在当前目录下生成一个比赛日，比赛日可以是独立的工程；')
		log.info(u'           有参数表示在当前比赛下依次生成名叫参数1，参数2，…的比赛日，')
		log.info(u'           有参数必须保证当前目录是比赛。')
		log.info(u'  problem  无参数表示在当前目录下生成一道题目，题目可以是独立的工程；')
		log.info(u'           有参数表示在当前比赛日下依次生成名叫参数1，参数2，…的题目，')
		log.info(u'           有参数必须保证当前目录是比赛日。')
		log.info(u'  data     在所有题目工程的data文件夹中搜索数据并添加到配置文件。')
		log.info(u'  samples  在所有题目工程的down文件夹中搜索样例并添加到配置文件。')
		log.info(u'  code     在所有题目工程的非数据文件夹中搜索源代码并添加到配置文件。')
