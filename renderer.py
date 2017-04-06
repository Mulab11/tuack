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
import jinja2
import tools
import uuid

work_class = {
	'noi' : {'noi'},
	'ccpc' : {'ccpc'},
	'uoj' : {'uoj'},
	'tuoj' : {'tuoj-tex', 'tuoj-html'},
	'ccc' : {'ccc-tex', 'ccc-html'},
	'ccc-tex' : {'ccc-tex'},
	'ccc-html' : {'ccc-html'},
	'tex' : {'noi', 'ccpc', 'tuoj-tex', 'ccc-tex'},
	'html' : {'uoj', 'tuoj-html', 'ccc-html'}
}
io_styles = {
	'noi' : 'fio',
	'ccpc' : 'stdio',
	'uoj' : 'stdio',
	'tuoj' : 'stdio',
	'ccc' : 'stdio'
}
base_templates = {
	'noi' : 'tuack',
	'tuoj' : 'tuack',
	'ccpc' : 'ccpc',
	'ccc' : 'ccc'
}
work_list = {
	'noi' : lambda : tex('noi'),
	'ccpc' : lambda : tex('ccpc'),
	'uoj' : lambda : html('uoj'),
	'tuoj-tex' : lambda : tex('tuoj'),
	'tuoj-html' : lambda : html('tuoj'),
	'ccc-tex' :  lambda : tex('ccc'),
	'ccc-html' : lambda : html('ccc')
}


secondary_dict = {}

def init():
	global env
	common.mkdir('statements')
	shutil.rmtree('tmp', ignore_errors = True)
	env = jinja2.Environment(
		loader = jinja2.FileSystemLoader(os.path.join(os.getcwd(), 'tmp')), extensions=['jinja2.ext.do', 'jinja2.ext.with_']
	)
	time.sleep(0.1)
	shutil.copytree(os.path.join(common.path, 'templates'), 'tmp')
	
def final():
	shutil.rmtree('tmp', ignore_errors = True)

def file_name(comp, prob, name):
	if comp == 'noi':
		return prob['name'] + '/' + name
	elif comp == 'uoj':
		return name
	else:
		return name
	
def table(path, name, temp, context, options):
	common.copy(path, name + '.json', os.path.join('tmp', 'table.json'))
	res = env.get_template('table.json').render(context, options = options)
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
	ret = env.get_template(temp).render(context, table = table, cnt = cnt, width = max_len, options = options)
	os.remove(os.path.join('tmp', 'table.json'))
	return ret
	
def secondary(s, sp, work):
	if sp != None:
		if type(sp) == str:
			sp = [sp]
		in_set = False
		for i in sp:
			if i in work_class and common.work in work_class[i]:
				in_set = True
				break
		if not in_set:
			return ''
	if work == 'tex':
		id = str(uuid.uuid4())
		secondary_dict[id] = s
		return id
	else:
		return ' {{ ' + s + ' }} '
	
def tex(comp):
	def render(conf, contest, path):
		tex_problems = []
		day_name = conf['name'] if conf['folder'] == 'day' else '测试'
		probs = conf['sub'] if conf['folder'] == 'day' else [conf]
		for prob in probs:
			try:
				common.copy(
					os.path.join(prob['path'], 'statement'),
					'zh-cn.md',
					os.path.join('tmp', 'problem.md.jinja')
				)
			except:
				common.copy(
					prob['path'],
					'description.md',
					os.path.join('tmp', 'problem.md.jinja')
				)
			context = {
				'prob' : prob,
				'day' : conf if conf['folder'] == 'day' else None,
				'contest' : contest,
				'io_style' : io_style,
				'comp' : comp,
				'tools' : tools,
				'common' : common,
				'file_name' : lambda name : file_name(comp, prob, name),
				'down_file' : lambda name : open(os.path.join(prob['path'], 'down', name), 'rb').read().decode('utf-8'),
				'resource' : lambda name : os.path.join('..', prob['path'], 'resources', name).replace('\\', '/'),
				'render' : lambda s, sp = None : secondary(s, sp, 'tex'),
				'precautions' : prec
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
			tex = open(os.path.join('tmp', 'problem.tex'), 'rb').read().decode('utf-8')
			for key, val in secondary_dict.items():
				tex = tex.replace(key, '{{ ' + val + ' }}')
			open(os.path.join('tmp', 'problem.tex.jinja'), 'wb').write(
				tex.encode('utf-8')
			)
			res = env.get_template('problem.tex.jinja').render(
				context,
				template = lambda temp_name, **context : env.get_template(temp_name + '.tex.jinja').render(context),
				table = lambda name, options = {} : table(os.path.join(prob['path'], 'tables'), name, 'table.tex.jinja', context, options)
			)
			tex_problems.append(res)
		#shutil.copy(os.path.join(day_name, 'day_title.tex'), 'tmp')
		#all_problem_statement = env.get_template('day_title.tex').render(
		
		context.pop('prob')
		context.pop('file_name')
		context.pop('down_file')
		context.pop('resource')
		context.pop('render')
		context['probs'] = conf['sub'] if conf['folder'] == 'day' else [conf]
		context['problems'] = tex_problems
		all_problem_statement = env.get_template('%s.tex.jinja' % base_template).render(context)
		try:
			open(os.path.join('tmp', 'problems.tex'), 'wb') \
				.write(all_problem_statement.encode('utf-8'))
		except Exception as e:
			print('You can find the tex file with utf-8 code in tmp/problems.tmp.tex')
			open(os.path.join('tmp', 'problems.tmp.tex'), 'wb') \
				.write(all_problem_statement.encode('utf-8'))
			raise e
		os.chdir('tmp')
		os.system('xelatex problems.tex')
		os.system('xelatex problems.tex')
		os.chdir('..')
		shutil.copy(os.path.join('tmp', 'problems.pdf'), path)
		if common.start_file:
			if common.system == 'Windows':
				os.startfile(path)
			else:
				subprocess.call(["xdg-open", path])

	common.mkdir(os.path.join('statements', comp))
	io_style = io_styles[comp]
	base_template = base_templates[comp]
	prec = None
	if os.path.exists(os.path.join('precautions', 'zh-cn.md')):
		common.copy('precautions', 'zh-cn.md', 'tmp')
		os.system('pandoc %s -t latex -o %s' % (
			os.path.join('tmp', 'zh-cn.md'),
			os.path.join('tmp', 'precautions.tex')
		))
		prec = open(os.path.join('tmp', 'precautions.tex'), 'rb').read().decode('utf-8')
	#shutil.copy(os.path.join('title.tex'), 'tmp')
	if common.conf['folder'] != 'problem':
		for day in common.days():
			result_path = os.path.join('statements', comp, day['name'] + '.pdf')
			render(day, common.conf if common.conf['folder'] == 'contest' else None, result_path)
	else:
		result_path = os.path.join('statements', comp, common.conf['name'] + '.pdf')
		render(common.conf, None, result_path)
		
def html(comp):
	def render(prob):
		path = os.path.join('statements', comp, prob['route'])
		if os.path.exists(os.path.join(prob['path'], 'resources')):
			shutil.rmtree(path, ignore_errors = True)
			time.sleep(0.1)
			shutil.copytree(os.path.join(prob['path'], 'resources'), path)
		try:
			common.copy(
				os.path.join(prob['path'], 'statement'),
				'zh-cn.md',
				os.path.join('tmp', 'problem.md.jinja')
			)
		except:
			common.copy(
				prob['path'],
				'description.md',
				os.path.join('tmp', 'problem.md.jinja')
			)
		time.sleep(0.1)
		context = {
			'prob' : prob,
			'io_style' : io_style,
			'tools' : tools,
			'common' : common,
			'file_name' : lambda name : file_name(comp, prob, name),
			'down_file' : lambda name : open(os.path.join(prob['path'], 'down', name), 'rb').read().decode('utf-8'),
			'resource' : lambda name : prob['name'] + '/' + name,
			'render' : lambda s, sp = None : secondary(s, sp, 'uoj')
		}
		open(os.path.join('tmp', 'problem.md'), 'wb') \
			.write(env.get_template('problem_base.md.jinja')
				.render(context)
				.encode('utf-8')
			)
		open(path + '.md', 'wb') \
			.write(env.get_template('problem.md')
				.render(
					context,
					template = lambda temp_name, **context : env.get_template(temp_name + '.html.jinja').render(context),
					table = lambda name, options={} : table(os.path.join(prob['path'], 'tables'), name, 'table.html.jinja', context, options)
				).encode('utf-8')
			)
		if common.start_file:
			if common.system == 'Windows':
				os.startfile(path + '.md')
			else:
				subprocess.call(["xdg-open", path + '.md'])
						
	common.mkdir(os.path.join('statements', comp))
	io_style = io_styles[comp]
	base_template = base_templates[comp]
	for prob in common.probs():
		render(prob)
	
if __name__ == '__main__':
	if common.init():
		common.infom('Rendering starts at %s.\n' % str(datetime.datetime.now()))
		init()
		for common.work in common.works:
			work_list[common.work]()
		final()
	else:
		#print('\t-l zh-cn,en: Output in multiple languages.')
		print('Use arguments other than options to run what to output.')
		print('Enabled output types: noi, noip, uoj, tuoj, ccc-tex, ccc-html, ccpc.')
