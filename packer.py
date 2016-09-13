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
import jinja2
import math

doc_format = re.compile(r'^(.*)\.(doc|docs|ppt|pptx|pdf|tex|md|html|htm|zip|dir)$')
empty_cpp = 'int main(){}'
jinja_env = Environment(loader=PackageLoader('renderer', '.'))

def find_doc(path, name):
	for f in os.listdir(path):
		m = doc_format.match(f)
		if m and m.group(1) == name:
			return name, '.' + m.group(2)
	return None

def copy_one_day_files(probs, day_name):
	remkdir(os.path.join(output_folder, day_name, 'data'))
	print('copy data files')
	for prob in probs:
		if day_name + '/' + prob['name'] not in common.prob_set:
			continue
		# TODO: if test cases is a list of scores instead of an integer
		data_path = os.path.join(day_name, prob['name'], 'data')
		for i in range(1, prob['test cases'] + 1):
			for suf in ['.in', '.ans']:
				copy(data_path, prob['name'] + str(i) + suf, os.path.join(output_folder, day_name, 'data'))
		copy(data_path, 'chk', os.path.join(output_folder, day_name, 'data', prob['name'] + '_e'))
		for name in os.listdir(data_path):
			if os.path.join(data_path, name) not in common.copied_data:
				warning('Unusual file \'%s\' found.' % os.path.join(data_path, name))
				copy(data_path, name, os.path.join(output_folder, day_name, 'data'))
	print('dos2unix data files')
	if os.system('dos2unix %s 2> log' % os.path.join(output_folder, day_name, 'data', '*')) != 0:
		warning('dos2unix failed.')
	print('copy down files')
	remkdir(os.path.join(output_folder, day_name, 'down'))
	for prob in probs:
		if day_name + '/' + prob['name'] not in common.prob_set:
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
			if os.path.join(data_path, name) not in common.copied_data:
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
		
def prob2uoj_conf(prob):
	s = ''
	s += 'use_builtin_judger on\n'
	if prob['type'] == 'output':
		s += 'submit_answer on\n'
	s += 'n_tests %d\n' % prob['test cases']
	s += 'n_ex_tests %d\n' % prob['sample count']
	s += 'n_sample_tests %d\n' % prob['sample count']
	s += 'input_pre %s\n' % prob['name']
	s += 'input_suf in\n'
	s += 'output_pre %s\n' % prob['name']
	s += 'output_suf out\n'
	if 'time limit' in prob:
		s += 'time_limit %d\n' % math.ceil(prob['time limit'])
	if 'memory limit' in prob:
		s += 'memory_limit %d\n' % (common.memory2bytes(prob['memory limit']) // 1024 // 1024)
	if 'output limit' in prob:
		s += 'output_limit %d\n' % (common.memory2bytes(prob['output limit']) // 1024 // 1024)
	else:
		s += 'output_limit 1024\n'
	return s
		
def uoj_copy_one_day_files(probs, day_name):
	print('copy data files')
	for prob in probs:
		if day_name + '/' + prob['name'] not in common.prob_set:
			continue
		# TODO: if test cases is a list of scores instead of an integer
		data_path = os.path.join(day_name, prob['name'], 'data')
		target_path = os.path.join(output_folder, day_name, prob['name'], '1')
		remkdir(os.path.join(output_folder, day_name, prob['name']))
		remkdir(target_path)
		for i in range(1, prob['test cases'] + 1):
			for suf in ['.in', '.ans']:
				copy(data_path, prob['name'] + str(i) + suf, target_path)
		if not copy(os.path.join(data_path, 'chk'), 'chk.cpp', target_path) and 'uoj_builtin_checker' not in prob:
			prob['uoj_builtin_checker'] = 'wcmp'
		if not copy(os.path.join(data_path, 'val'), 'val.cpp', target_path):
			with open(os.path.join(target_path, 'val.cpp'), 'w') as f:
				f.write(empty_cpp)
		for name in os.listdir(data_path):
			if os.path.join(data_path, name) not in common.copied_data:
				require_path = os.path.join(target_path, 'require')
				if not os.path.exists(require_path):
					os.makedirs(require_path)
				warning('Unusual file \'%s\' found.' % os.path.join(data_path, name))
				copy(data_path, name, require_path)
		download_path = os.path.join(target_path, 'download')
		remkdir(download_path)
		case_no = (0 if prob['type'] == 'output' else prob['sample count'])
		suffices = ['.in', '.ans']
		for i in range(1, case_no + 1):
			for suf in suffices:
				copy(data_path, prob['name'] + str(i) + suf, download_path)
				copy(data_path, prob['name'] + str(i) + suf, os.path.join(target_path, 'ex_' + prob['name'] + str(i) + suf))
		copy(data_path, 'checker', download_path)
		for name in os.listdir(data_path):
			if os.path.join(data_path, name) not in common.copied_data:
				warning('Unusual file \'%s\' found.' % os.path.join(data_path, name))
				copy(data_path, name, download_path)
		with open(os.path.join(target_path, 'problem.conf'), 'w') as f:
			f.write(prob2uoj_conf(prob))
		with open(os.path.join(target_path, 'std.cpp'), 'w') as f:
			f.write(empty_cpp)
		if os.system('dos2unix %s 2> log' % os.path.join(output_folder, day_name, prob['name'], '1', '*')) != 0:
			warning('dos2unix failed.')
	if os.path.exists('log'):
		os.remove('log')
	
def copy_files():
	for day_name, day_data in common.probs.items():
		if day_name not in common.day_set:
			continue
		copy_one_day_files(day_data, day_name)
		
def uoj_copy_files():
	for day_name, day_data in common.probs.items():
		if day_name not in common.day_set:
			continue
		uoj_copy_one_day_files(day_data, day_name)

def zip_tree(z, path):
	for name in os.listdir(path):
		full_path = os.path.join(path, name)
		if os.path.isdir(full_path):
			zip_tree(z, full_path)
		else:
			z.write(full_path)

def make_zip():
	for day_name, day_data in common.probs.items():
		if day_name not in common.day_set:
			continue
		with zipfile.ZipFile(os.path.join(output_folder, day_name + '.zip'), 'w') as z:
			zip_tree(z, os.path.join(output_folder, day_name))

def noi():
	global output_folder
	common.no_compiling = False
	output_folder = 'noi'
	remkdir('noi')
	copy_files()

def test():
	global output_folder
	common.no_compiling = False
	output_folder = '.'
	copy_files()

def release():
	global output_folder
	infom('make release files.')
	remkdir('release')
	common.no_compiling = True
	output_folder = 'release'
	copy_files()
	make_zip()
			
def uoj():
	global output_folder
	common.no_compiling = False
	output_folder = 'uoj'
	remkdir('uoj')
	uoj_copy_files()
			
work_list = {
	'noi' : noi,
	'test' : test,
	'uoj' : uoj,
	'release' : release
}

if __name__ == '__main__':
	if deal_argv():
		infom('Packing starts at %s.\n' % str(datetime.datetime.now()))
		for common.work in common.works:
			work_list[common.work]()
	else:
		print('Use arguments other than options to run what to output.')
		print('Enabled output types:')
		print('\ttest: Generate output for test. Must run this output before tester.py.')
		print('\trelease: Generate what is suitable to publish.')
		print('\tnoi: Generate output in noi style.')
		print('\tuoj: Generte output in uoj style.')
