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
try:
	import jinja2
except:
	pass
import tools
import uuid

work_class = {
	'noi' : {'noi'},
	'ccpc' : {'ccpc'},
	'uoj' : {'uoj'},
	'tuoj' : {'tuoj-tex', 'tuoj-html'},
	'tuoj-tex' : {'tuoj-tex'},
	'tuoj-html' : {'tuoj-html'},
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
		log.info('You can find the json file with error in tmp/table.tmp.json')
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
	common.check_install('pandoc')
	common.check_install('xelatex')
	def render(conf, contest, path):
		tex_problems = []
		day_name = conf['name'] if conf.folder == 'day' else '测试'
		probs = list(conf.probs())
		if len(probs) == 0:
			log.info('Nothing to do for %s' % conf.route)
			return
		for prob in probs:
			log.info('rendering %s %s' % (comp, prob.route))
			try:
				common.copy(
					os.path.join(prob.path, 'statement'),
					'zh-cn.md',
					os.path.join('tmp', 'problem.md.jinja')
				)
				lang = 'zh-cn'
			except:
				try:
					common.copy(
						os.path.join(prob.path, 'statement'),
						'en.md',
						os.path.join('tmp', 'problem.md.jinja')
					)
					lang = 'en'
				except:
					common.copy(
						prob.path,
						'description.md',
						os.path.join('tmp', 'problem.md.jinja')
					)
					lang = 'zh-cn'
			context = {
				'prob' : prob,
				'day' : conf if conf.folder == 'day' else None,
				'contest' : contest,
				'io_style' : io_style,
				'comp' : comp,
				'tools' : tools,
				'common' : common,
				'file_name' : lambda name : file_name(comp, prob, name),
				'down_file' : lambda name : open(os.path.join(prob.path, 'down', name), 'rb').read().decode('utf-8'),
				'resource' : lambda name : os.path.join('..', prob.path, 'resources', name).replace('\\', '/'),
				'render' : lambda s, sp = None : secondary(s, sp, 'tex'),
				'precautions' : prec,
				'json' : json,
				'lang' : lang
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
				table = lambda name, options = {} : table(os.path.join(prob.path, 'tables'), name, 'table.tex.jinja', context, options)
			)
			tex_problems.append(res)

		log.info('rendering %s %s' % (comp, conf.route))
		context.pop('prob')
		context.pop('file_name')
		context.pop('down_file')
		context.pop('resource')
		context.pop('render')
		context['probs'] = list(conf.probs())
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
		os.system('xelatex -quiet problems.tex')
		os.system('xelatex -quiet problems.tex')
		os.chdir('..')
		shutil.copy(os.path.join('tmp', 'problems.pdf'), path)
		if common.start_file:
			common.xopen_file(path)
	common.mkdir(os.path.join('statements', comp))
	io_style = io_styles[comp]
	base_template = base_templates[comp]
	context = {
		'io_style' : io_style,
		'comp' : comp,
		'tools' : tools,
		'common' : common,
		'json' : json
	}
	prec = None
	if os.path.exists(common.pjoin(common.conf.path, 'precautions', 'zh-cn.md')):
		common.copy(common.pjoin(common.conf.path, 'precautions'), 'zh-cn.md', 'tmp')
		open(common.pjoin('tmp', 'precautions.md'), 'wb') \
			.write(env.get_template('zh-cn.md').render(context, conf = common.conf).encode('utf-8'))
		os.system('pandoc %s -t latex -o %s' % (
			os.path.join('tmp', 'precautions.md'),
			os.path.join('tmp', 'precautions.tex')
		))
		prec = open(os.path.join('tmp', 'precautions.tex'), 'rb').read().decode('utf-8')
	if common.conf.folder != 'problem':
		for day in common.days():
			result_path = os.path.join('statements', comp, day['name'] + '.pdf')
			render(day, common.conf if common.conf.folder == 'contest' else None, result_path)
	else:
		result_path = os.path.join('statements', comp, common.conf['name'] + '.pdf')
		render(common.conf, None, result_path)
		
def html(comp):
	def render(prob):
		log.info('rendering %s %s' % (comp, prob.route))
		path = os.path.join('statements', comp, prob.route)
		if os.path.exists(os.path.join(prob.path, 'resources')):
			shutil.rmtree(path, ignore_errors = True)
			time.sleep(0.1)
			shutil.copytree(os.path.join(prob.path, 'resources'), path)
		try:
			common.copy(
				os.path.join(prob.path, 'statement'),
				'zh-cn.md',
				os.path.join('tmp', 'problem.md.jinja')
			)
			lang = 'zh-cn'
		except:
			try:
				common.copy(
					os.path.join(prob.path, 'statement'),
					'en.md',
					os.path.join('tmp', 'problem.md.jinja')
				)
				lang = 'en'
			except:
				common.copy(
					prob.path,
					'description.md',
					os.path.join('tmp', 'problem.md.jinja')
				)
				lang = 'zh-cn'
		time.sleep(0.1)
		context = {
			'prob' : prob,
			'io_style' : io_style,
			'tools' : tools,
			'common' : common,
			'file_name' : lambda name : file_name(comp, prob, name),
			'down_file' : lambda name : open(os.path.join(prob.path, 'down', name), 'rb').read().decode('utf-8'),
			'resource' : lambda name : prob['name'] + '/' + name,
			'render' : lambda s, sp = None : secondary(s, sp, 'uoj'),
			'json' : json,
			'lang' : lang
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
					table = lambda name, options={} : table(os.path.join(prob.path, 'tables'), name, 'table.html.jinja', context, options)
				).encode('utf-8')
			)
		if common.start_file:
			common.xopen_file(path + '.md')

	common.mkdir(os.path.join('statements', comp))
	io_style = io_styles[comp]
	base_template = base_templates[comp]
	if common.conf.folder == 'contest':
		for day in common.days():
			if not os.path.exists(common.pjoin('statements', comp, day.route)):
				os.makedirs(common.pjoin('statements', comp, day.route))
	for prob in common.probs():
		render(prob)

if __name__ == '__main__':
	if common.init():
		common.check_install('jinja2')
		init()
		for common.work in common.works:
			work_list[common.work]()
		final()
	else:
		pass
