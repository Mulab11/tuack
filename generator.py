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

def find_all_data(kind, folder, key):
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
	for prob in common.probs():
		log.info(u'在题目`%s`下搜索%s数据。' % (key, prob.route))
		new_data = set()
		exist_data = set(map(str, prob.__getattribute__(key)))
		find_data()
		new_data = parse(new_data)
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
			if os.path.isfile(common.pjoin(full_path, f)):
				for key in common.compilers:
					if not f.endswith('.' + key):
						continue
					if common.rjoin(user, path, f) not in exist_code:
						prob['users'][user][common.rjoin(path, f)] = common.rjoin(user, path, f)
					break
			else:
				if common.user_skip.match(f):
					continue
				find_code(user, common.rjoin(path, f))

	for prob in common.probs():
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

def new_dir(folder):
	def copy(src, tgt = None):
		if not tgt:
			tgt = src
		if not os.path.exists(common.pjoin(path, tgt)):
			common.copy(
				common.pjoin(common.path, 'sample'),
				src,
				common.pjoin(path, tgt)
			)

	if len(common.args) == 0:
		dirs = ['.']
	else:
		if not common.conf:
			log.error(u'当前文件夹下没有 `conf.json` 文件。')
			raise common.NoFileException('No `conf.json` in this directory.')
		dirs = common.args
	for path in dirs:
		if not os.path.exists(path):
			os.makedirs(path)
		copy(folder + '.gitignore', '.gitignore')
		copy(folder + '.json', 'conf.json')
		if folder == 'problem':
			copy('.gitattributes')
			st_path = common.pjoin(path, 'statement')
			if not os.path.exists(st_path):
				os.makedirs(st_path)
			for f in os.listdir(common.pjoin(common.path, 'sample', 'statement')):
				copy(common.pjoin('statement', f), common.pjoin('statement', f))
		if path != '.':
			conf = json.loads(open(common.pjoin(path, 'conf.json'), 'rb').read().decode('utf-8'))
			conf['name'] = path
			conf.path = path
			common.save_json(conf)
	if len(common.args) != 0:
		common.conf['subdir'] = sorted(list(set(common.conf['subdir'] + common.args)))
		common.save_json(common.conf)

work_list = {
	'data' : lambda : find_all_data('data', 'data', 'test_cases'),
	'samples' : lambda : find_all_data('samples', 'down', 'sample_cases'),
	'code' : find_all_code,
	'contest' : lambda : new_dir('contest'),
	'day' : lambda : new_dir('day'),
	'problem' : lambda : new_dir('problem')
}

if __name__ == '__main__':
	try:
		result = common.init()
	except common.NoJsonException as e:
		common.conf = None
		result = True
	if result:
		for common.work in common.works:
			work_list[common.work]()
	else:
		pass
