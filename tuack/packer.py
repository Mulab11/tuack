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
from .base import *
from . import base
import math

doc_format = re.compile(r'^(.*)\.(doc|docs|ppt|pptx|pdf|tex|md|html|htm|zip|dir)$')
empty_cpp = 'int main(){}'

def find_doc(path, name):
	for f in os.listdir(path):
		m = doc_format.match(f)
		if m and m.group(1) == name:
			return name, '.' + m.group(2)
	return None

def test_copy_problem_files(prob):
	data_path = os.path.join(prob.path, 'data')
	try:
		copy(data_path, 'chk', base.pjoin(output_folder, prob.route))
		prob.chk = True
	except Exception as e:
		prob.chk = False
	
def copy_one_day_files(probs, day_name):
	remkdir(os.path.join(output_folder, day_name, 'data'))
	print('copy data files')
	for prob in probs:
		if base.rjoin(day_name, prob['name']) not in base.prob_set:
			continue
		# TODO: if test cases is a list of scores instead of an integer
		data_path = os.path.join(day_name, prob['name'], 'data')
		for i in range(1, prob['test cases'] + 1):
			for suf in ['.in', '.ans']:
				copy(data_path, prob['name'] + str(i) + suf, os.path.join(output_folder, day_name, 'data'))
		copy(data_path, 'chk', os.path.join(output_folder, day_name, 'data', prob['name'] + '_e'))
		for name in os.listdir(data_path):
			if os.path.join(data_path, name) not in base.copied_data:
				warning('Unusual file \'%s\' found.' % os.path.join(data_path, name))
				copy(data_path, name, os.path.join(output_folder, day_name, 'data'))
	print('dos2unix data files')
	if os.system('dos2unix %s 2> log' % os.path.join(output_folder, day_name, 'data', '*')) != 0:
		warning('dos2unix failed.')
	print('copy down files')
	remkdir(os.path.join(output_folder, day_name, 'down'))
	for prob in probs:
		if base.rjoin(day_name, prob['name']) not in base.prob_set:
			continue
		# TODO: if test cases is a list of scores instead of an integer
		data_path = os.path.join(day_name, prob['name'], 'down')
		target_path = os.path.join(output_folder, day_name, 'down', prob['name'])
		if not os.path.exists(target_path):
			os.makedirs(target_path)
		#print(prob)
		case_no = (prob['test cases'] if prob['type'] == 'output' else prob['sample count'])
		suffices = (['.in'] if prob['type'] == 'output' else ['.in', '.ans'])
		for i in range(1, case_no + 1):
			for suf in suffices:
				copy(data_path, prob['name'] + str(i) + suf, target_path)
		copy(data_path, 'checker', target_path)
		for name in os.listdir(data_path):
			if os.path.join(data_path, name) not in base.copied_data:
				warning('Unusual file \'%s\' found.' % os.path.join(data_path, name))
				copy(data_path, name, target_path)
	print('dos2unix down files')
	for prob in probs:
		if os.system('dos2unix %s 2> log' % os.path.join(output_folder, day_name, 'down', prob['name'], '*')) != 0:
			warning('dos2unix failed.')
			break
	remkdir(os.path.join(output_folder, day_name, 'discussion'))
	for prob in probs:
		res = find_doc(os.path.join(day_name, prob['name']), 'discussion')
		if res:
			copy(os.path.join(day_name, prob['name']), res[0] + res[1], os.path.join(output_folder, day_name, 'discussion', prob['name'] + res[1]))
		else:
			warning('Can\'t find discussion ppt for problem `%s`.' % prob['name'])
	if os.path.exists('log'):
		os.remove('log')
		
def pc2_copy_one_day_files(probs, day_name):
	remkdir(os.path.join('pc2', day_name))
	remkdir(os.path.join('pc2', day_name, 'data'))
	print('copy data files')
	for prob in probs:
		if base.rjoin(day_name, prob['name']) not in base.prob_set:
			continue
		name = prob['name'].capitalize()
		# TODO: if test cases is a list of scores instead of an integer
		remkdir(os.path.join('pc2', day_name, 'data', name))
		data_path = os.path.join(day_name, name, 'data')
		target_path = os.path.join('pc2', day_name, 'data', name)
		for i in range(1, prob['test cases'] + 1):
			for suf in ['.in', '.ans']:
				copy(data_path, prob['name'] + str(i) + suf, target_path)
		copy(data_path, 'chk', target_path)
		for name in os.listdir(data_path):
			if os.path.join(data_path, name) not in base.copied_data:
				warning('Unusual file \'%s\' found.' % os.path.join(data_path, name))
				copy(data_path, name, target_path)
		if os.system('dos2unix %s 2> log' % os.path.join(target_path, '*')) != 0:
			warning('dos2unix failed.')
	print('copy down files')
	remkdir(os.path.join('pc2', day_name, 'down'))
	for prob in probs:
		if base.rjoin(day_name, prob['name']) not in base.prob_set:
			continue
		name = prob['name'].capitalize()
		# TODO: if test cases is a list of scores instead of an integer
		data_path = os.path.join(day_name, prob['name'], 'down')
		target_path = os.path.join('pc2', day_name, 'down', name)
		remkdir(target_path)
		case_no = (prob['test cases'] if prob['type'] == 'output' else prob['sample count'])
		suffices = (['.in'] if prob['type'] == 'output' else ['.in', '.ans'])
		for i in range(1, case_no + 1):
			for suf in suffices:
				copy(data_path, prob['name'] + str(i) + suf, target_path)
		copy(data_path, 'checker', target_path)
		for name in os.listdir(data_path):
			if os.path.join(data_path, name) not in base.copied_data:
				warning('Unusual file \'%s\' found.' % os.path.join(data_path, name))
				copy(data_path, name, target_path)
	print('dos2unix down files')
	for prob in probs:
		if os.system('dos2unix %s 2> log' % os.path.join('pc2', day_name, 'down', prob['name'], '*')) != 0:
			warning('dos2unix failed.')
			break
	remkdir(os.path.join('pc2', day_name, 'discussion'))
	for prob in probs:
		res = find_doc(os.path.join(day_name, prob['name']), 'discussion')
		if res:
			copy(os.path.join(day_name, prob['name']), res[0] + res[1], os.path.join('pc2', day_name, 'discussion', prob['name'] + res[1]))
		else:
			warning('Can\'t find discussion ppt for problem `%s`.' % prob['name'])
	if os.path.exists('log'):
		os.remove('log')
		
def prob2uoj_conf(prob):
	s = ''
	s += 'use_builtin_judger on\n'
	if 'uoj checker' not in prob:
		s += 'use_builtin_checker wcmp\n'
	elif prob['uoj checker'] != False:
		s += 'use_builtin_checker %s\n' % prob['uoj checker']
	if prob['type'] == 'output':
		s += 'submit_answer on\n'
	s += 'n_tests %d\n' % prob['test cases']
	s += 'n_ex_tests %d\n' % prob['sample count']
	s += 'n_sample_tests %d\n' % prob['sample count']
	s += 'input_pre %s\n' % prob['name']
	s += 'input_suf in\n'
	s += 'output_pre %s\n' % prob['name']
	s += 'output_suf ans\n'
	if 'time limit' in prob:
		s += 'time_limit %d\n' % math.ceil(prob['time limit'])
	if 'memory limit' in prob:
		s += 'memory_limit %d\n' % (base.memory2bytes(prob['memory limit']) // 1024 // 1024)
	if 'output limit' in prob:
		s += 'output_limit %d\n' % (base.memory2bytes(prob['output limit']) // 1024 // 1024)
	else:
		s += 'output_limit 64\n'
	return s

def uoj_copy_one_day_files(probs, day_name):
	print('copy data files')
	for prob in probs:
		if base.rjoin(day_name, prob['name']) not in base.prob_set:
			continue
		# TODO: if test cases is a list of scores instead of an integer
		data_path = os.path.join(day_name, prob['name'], 'data')
		target_path = os.path.join(output_folder, day_name, prob['name'], '1')
		#remkdir(os.path.join(output_folder, day_name, prob['name']))
		remkdir(target_path)
		for i in range(1, prob['test cases'] + 1):
			for suf in ['.in', '.ans']:
				copy(data_path, prob['name'] + str(i) + suf, target_path)
		if not copy(os.path.join(data_path, 'chk'), 'chk.cpp', target_path) and 'uoj_builtin_checker' not in prob:
			prob['uoj_builtin_checker'] = 'wcmp'
		if not copy(os.path.join(data_path, 'val'), 'val.cpp', target_path):
			pass
			#with open(os.path.join(target_path, 'val.cpp'), 'w') as f:
			#	f.write(empty_cpp)
		for name in os.listdir(data_path):
			if os.path.join(data_path, name) not in base.copied_data:
				require_path = os.path.join(target_path, 'require')
				if not os.path.exists(require_path):
					os.makedirs(require_path)
				warning('Unusual file \'%s\' found.' % os.path.join(data_path, name))
				copy(data_path, name, require_path)
		download_path = os.path.join(target_path, 'download')
		remkdir(download_path)
		case_no = (0 if prob['type'] == 'output' else prob['sample count'])
		suffices = ['.in', '.ans']
		data_path = os.path.join(day_name, prob['name'], 'down')
		for i in range(1, case_no + 1):
			for suf in suffices:
				#copy(data_path, prob['name'] + str(i) + suf, download_path)
				copy(data_path, prob['name'] + str(i) + suf, os.path.join(target_path, 'ex_' + prob['name'] + str(i) + suf))
		copy(data_path, 'checker', download_path)
		for name in os.listdir(data_path):
			if os.path.join(data_path, name) not in base.copied_data:
				warning('Unusual file \'%s\' found.' % os.path.join(data_path, name))
				copy(data_path, name, download_path)
		with open(os.path.join(target_path, 'problem.conf'), 'w') as f:
			f.write(prob2uoj_conf(prob))
		#with open(os.path.join(target_path, 'std.cpp'), 'w') as f:
		#	f.write(empty_cpp)
		if os.system('dos2unix %s 2> log' % os.path.join(output_folder, day_name, prob['name'], '1', '*')) != 0:
			warning('dos2unix failed.')
	if os.path.exists('log'):
		os.remove('log')

def copy_files(suffix = ''):
	for day in base.days():
		base.mkdir(os.path.join(output_folder, day.route))
	for prob in base.probs():
		eval(suffix + 'copy_problem_files')(prob)

def zip_tree(z, path):
	for name in os.listdir(path):
		full_path = os.path.join(path, name)
		if os.path.isdir(full_path):
			zip_tree(z, full_path)
		else:
			z.write(full_path)

def make_zip():
	for day_name, day_data in base.probs.items():
		if day_name not in base.day_set:
			continue
		with zipfile.ZipFile(os.path.join(output_folder, day_name + '.zip'), 'w') as z:
			zip_tree(z, os.path.join(output_folder, day_name))

def noi():
	global output_folder
	base.no_compiling = False
	output_folder = 'noi'
	remkdir('noi')
	copy_files()

def test():
	global output_folder
	base.no_compiling = False
	output_folder = 'bin'
	if base.conf.folder != 'problem':
		remkdir('bin')
		for day in base.days():
			remkdir(base.pjoin('bin', day.route))
	copy_files('test_')
	
def pc2():
	global output_folder
	base.no_compiling = True
	remkdir('pc2')
	copy_files('pc2_')

def release():
	global output_folder
	infom('make release files.')
	remkdir('release')
	base.no_compiling = True
	output_folder = 'release'
	copy_files()
	make_zip()

def svn_init():
	for day_name, probs in base.probs.items():
		if day_name not in base.day_set:
			continue
		for prob in probs:
			if base.rjoin(day_name, prob['name']) not in base.prob_set:
				continue
			if not os.path.exists(os.path.join('uoj', day_name, prob['name'], '.svn')):
				os.system(
					'svn checkout --username %s --password %s %s %s' % (
						uoj_config['user'],
						uoj_config['svn pwd'],
						'svn://%s/problem/%d' % (uoj_config['host'], prob['uoj id']),
						os.path.join(os.path.join('uoj', day_name, prob['name']))
					)
				)
			else:
				os.system('svn delete %s' % os.path.join(os.path.join('uoj', day_name, prob['name'], '1')))
	
def svn_upload():
	for day_name, probs in base.probs.items():
		if day_name not in base.day_set:
			continue
		for prob in probs:
			if base.rjoin(day_name, prob['name']) not in base.prob_set:
				continue
			os.system('svn add %s' % os.path.join(os.path.join('uoj', day_name, prob['name'], '1')))
			os.system('svn commit %s -m "%s"' % (
				os.path.join(os.path.join('uoj', day_name, prob['name'], '1')),
				'Auto generated by oi_tools'
			))

def uoj():
	global output_folder, uoj_config
	base.no_compiling = False
	output_folder = 'uoj'
	if not os.path.exists('uoj'):
		os.makedirs('uoj')
	if not os.path.exists('uoj.json'):
		flag = False
		warning('uoj.json not found. Cannot upload to uoj')
	else:
		flag = True
	if flag:
		uoj_config = json.loads(open('uoj.json').read())
		svn_init()
	copy_files('uoj_')
	if flag:
		svn_upload()

work_list = {
	'noi' : noi,
	'test' : test,
	'uoj' : uoj,
	'pc2' : pc2,
	'release' : release
}

if __name__ == '__main__':
	if base.init():
		infom('Packing starts at %s.\n' % str(datetime.datetime.now()))
		for base.work in base.works:
			work_list[base.work]()
	else:
		print('Use arguments other than options to run what to output.')
		print('Enabled output types:')
		print('\ttest: Generate output for test. Must run this output before tester.py.')
		print('\trelease: Generate what is suitable to publish.')
		print('\tnoi: Generate output in noi style.')
		print('\tuoj: Generate output in uoj style.')
