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
import tools

'''
jinja_env = jinja2.Environment(loader=jinja2.PackageLoader('renderer', 'templates'))
temp = jinja_env.get_template('noiproblem.tex')
with open(os.path.join('oi_tools', 'output.tex'), 'wb') as f:
	f.write(temp.render(day = {'eng_title' : 'CCF-NOI-2016'}, probs = [{},{},{},{}]).encode('GBK'))
'''

def init():
	global env
	env = jinja2.Environment(loader=jinja2.PackageLoader('renderer', os.path.join('..', 'tmp')), extensions=['jinja2.ext.do', 'jinja2.ext.with_'])
	remkdir('descriptions')
	shutil.rmtree('tmp', ignore_errors = True)
	time.sleep(0.1)
	shutil.copytree(os.path.join('oi_tools', 'templates'), 'tmp')
	
def final():
	shutil.rmtree('tmp', ignore_errors = True)

def file_name(io_style, prob, name):
	if io_style == 'noi':
		return prob['name'] + '/' + name
	elif io_style == 'uoj':
		return name
	else:
		return name
	
def table(path, name, temp, context):
	copy(path, name + '.json', os.path.join('tmp', 'table.json'))
	res = env.get_template('table.json').render(context)
	try:
		table = json.loads(res)
	except Exception as e:
		open(os.path.join('tmp', 'table.tmp.json'), 'w').write(res)
		print('You can find the json file in tmp/table.tmp.json')
		raise e
	cnt = [[1] * len(row) for row in table]
	max_len = len(table[-1])
	for i in range(len(table) - 2, -1, -1):
		max_len = max(max_len, len(table[i]))
		for j in range(min(len(table[i]), len(table[i + 1]))):
			if table[i + 1][j] == None:
				cnt[i][j] += cnt[i + 1][j]
	return env.get_template(temp).render(table = table, cnt = cnt, width = max_len)
	
def noi():
	remkdir(os.path.join('descriptions', 'noi'))
	io_style = 'noi'
	shutil.copy(os.path.join('title.tex'), 'tmp')
	for day_name, probs in common.probs.items():
		if day_name not in common.day_set:
			continue
		tex_problems = []
		for prob in probs:
			if day_name + '/' + prob['name'] not in common.prob_set:
				continue
			copy(os.path.join(day_name, prob['name']), 'description.md', os.path.join('tmp', 'problem.md.jinja'))
			context = {
				'prob' : prob,
				'io_style' : io_style,
				'tools' : tools,
				'file_name' : lambda name : file_name(io_style, prob, name),
				'down_file' : lambda name : open(os.path.join(day_name, prob['name'], 'down', name)).read(),
				'resource' : lambda name : '../' + day_name + '/' + prob['name'] + '/resources/' + name,
			}
			open(os.path.join('tmp', 'problem.md'), 'wb') \
				.write(env.get_template('problem_base.md.jinja')
					.render(context)
					.encode('utf-8')
				)
			time.sleep(0.1)
			os.system('pandoc %s -t latex -o %s' % (
				os.path.join('tmp', 'problem.md'),
				os.path.join('tmp', 'problem.tex')
			))
			open(os.path.join('tmp', 'problem.tex.jinja'), 'wb').write(
				open(os.path.join('tmp', 'problem.tex'), 'rb')
					.read()
					.decode('utf-8')
					.replace('\\{\\{', '{{')
					.replace('\\}\\}', '}}')
					.replace('`', '\'')
					.encode('utf-8')
			)
			try:
				res = env.get_template('problem.tex.jinja').render(
					context,
					template = lambda temp_name, **context : env.get_template(temp_name + '.tex.jinja').render(context),
					table = lambda name : table(os.path.join(day_name, prob['name'], 'tables'), name, 'table.tex.jinja', context)
				)
			except:
				res = open(os.path.join('tmp', 'problem.tex.jinja'), 'rb').read().decode('utf-8')
			tex_problems.append(res)
		shutil.copy(os.path.join(day_name, 'day_title.tex'), 'tmp')
		all_problem_description = env.get_template('day_title.tex').render(
			problems = tex_problems,
			probs = [prob for prob in probs if day_name + '/' + prob['name'] in common.prob_set]
		)
		try:
			open(os.path.join('tmp', 'problems.tex'), 'wb') \
				.write(all_problem_description.encode(
					'utf-8' if common.system != 'Windows' else 'GBK'
				))
		except Exception as e:
			print('You can find the tex file with utf-8 code in tmp/problems.tmp.json')
			open(os.path.join('tmp', 'problems.tmp.tex'), 'w') \
				.write(all_problem_description.encode(
					'utf-8' if common.system != 'Windows' else 'GBK'
				))
			raise e
		os.chdir('tmp')
		os.system('pdflatex problems.tex')
		os.system('pdflatex problems.tex ')
		os.chdir('..')
		shutil.copy(os.path.join('tmp', 'problems.pdf'), os.path.join('descriptions', 'noi', day_name + '.pdf'))
		
def uoj():
	io_style = 'uoj'
	remkdir(os.path.join('descriptions', 'uoj'))
	for day_name, probs in common.probs.items():
		if day_name not in common.day_set:
			continue
		remkdir(os.path.join('descriptions', 'uoj', day_name))
		tex_problems = []
		for prob in probs:
			if day_name + '/' + prob['name'] not in common.prob_set:
				continue
			if os.path.exists(os.path.join(day_name, prob['name'], 'resources')):
				shutil.copytree(os.path.join(day_name, prob['name'], 'resources'), os.path.join('descriptions', 'uoj', day_name, prob['name']))
			copy(os.path.join(day_name, prob['name']), 'description.md', os.path.join('tmp', 'problem.md.jinja'))
			time.sleep(0.1)
			context = {
				'prob' : prob,
				'io_style' : io_style,
				'tools' : tools,
				'file_name' : lambda name : file_name(io_style, prob, name),
				'down_file' : lambda name : open(os.path.join(day_name, prob['name'], 'down', name)).read(),
				'resource' : lambda name : prob['name'] + '/' + name
			}
			open(os.path.join('tmp', 'problem.md'), 'wb') \
				.write(env.get_template('problem_base.md.jinja')
					.render(context)
					.encode('utf-8')
				)
			open(os.path.join('tmp', prob['name'] + '.md'), 'wb') \
				.write(env.get_template('problem.md')
					.render(
						context,
						template = lambda temp_name, **context : env.get_template(temp_name + '.html.jinja').render(context),
						table = lambda name : table(os.path.join(day_name, prob['name'], 'tables'), name, 'table.html.jinja', context)
					).encode('utf-8')
				)
			shutil.copy(os.path.join('tmp', prob['name'] + '.md'), os.path.join('descriptions', 'uoj', day_name))

work_list = {
	'noi' : noi,
	'uoj' : uoj
}
	
if __name__ == '__main__':
	if deal_argv():
		infom('Rendering starts at %s.\n' % str(datetime.datetime.now()))
		init()
		for common.work in common.works:
			work_list[common.work]()
		final()
	else:
		print('Use arguments other than options to run what to output.')
		print('Enabled output types:')
		print('\tnoi: Generate problem description in noi style.')
		print('\tuoj: Generate problem description in uoj style.')
