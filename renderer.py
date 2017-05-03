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
	'tupc' : {'tupc'},
	'tuoj-pc' : {'tupc', 'tuoj'},
	'tuoi' : {'tuoi'},
	'tuoj-oi' : {'tuoi', 'tuoj'},
	'tuoj' : {'tuoj'},
	'ccc' : {'ccc-tex', 'ccc-html'},
	'ccc-tex' : {'ccc-tex'},
	'ccc-html' : {'ccc-html'},
	'tex' : {'noi', 'ccpc', 'tupc', 'tuoi', 'ccc-tex'},
	'html' : {'uoj', 'tuoj', 'ccc-html'}
}
io_styles = {
	'noi' : 'fio',
	'ccpc' : 'stdio',
	'uoj' : 'stdio',
	'tuoj' : 'stdio',
	'ccc' : 'stdio',
	'tuoi' : 'stdio',
	'tupc' : 'stdio'
}
base_templates = {
	'noi' : 'tuoi',
	'tuoi' : 'tuoi',
	'tupc' : 'tupc',
	'ccpc' : 'ccpc',
	'ccc' : 'ccc'
}
work_list = {
	'ccpc' : lambda : tex('ccpc'),
	'uoj' : lambda : html('uoj'),
	'tupc' : lambda : tex('tupc'),
	'tuoi' : lambda : tex('tuoi'),
	'noi' : lambda : tex('noi'),
	'tuoj' : lambda : html('tuoj'),
	'ccc-tex' :  lambda : tex('ccc'),
	'ccc-html' : lambda : html('ccc')
}

secondary_dict = {}
env = None

def get_template(fname, lang = None):
	global env
	if common.lang:
		lang = common.lang
	if not lang:
		lang = 'zh-cn'
	if env == None or common.system == 'Darwin' or (lang and env['lang'] != lang):
		env = {
			'env' : jinja2.Environment(
				loader = jinja2.FileSystemLoader(os.path.join(os.getcwd(), 'tmp')),
				extensions = ['jinja2.ext.do', 'jinja2.ext.with_', 'jinja2.ext.i18n']
			),
			'lang' : lang
		}
		import gettext
		try:
			tra = gettext.translation('lang', os.getcwd() + '/tmp', [env['lang']])
			env['env'].install_gettext_translations(tra)
		except FileNotFoundError as e:
			log.warning(u'没有%s这种语言的翻译表可用。' % lang)
	return env['env'].get_template(fname)

def init():
	common.mkdir('statements')
	shutil.rmtree('tmp', ignore_errors = True)
	time.sleep(0.1)
	shutil.copytree(os.path.join(common.path, 'templates'), 'tmp')
	
def final():
	shutil.rmtree('tmp', ignore_errors = True)

def file_name(comp, prob, name):
	if comp == 'oi':
		return prob['name'] + '/' + name
	elif comp == 'uoj':
		return name
	else:
		return name
	
def table(path, name, temp, context, options):
	for suf in ['.py', '.json']:
		try:
			common.copy(path, name + suf, os.path.join('tmp', 'table' + suf))
			log.info(u'渲染表格`%s`，参数%s' % (common.pjoin(path, name + suf), str(options)))
			break
		except common.NoFileException as e:
			pass
	else:
		log.error(u'找不到表格`%s.*`' % common.pjoin(path, name))
	if suf == '.json':
		res = get_template('table.json', context['prob'].lang()).render(context, options = options)
		try:
			table = json.loads(res)
		except Exception as e:
			open(os.path.join('tmp', 'table.tmp.json'), 'w').write(res)
			log.error(u'json文件错误`tmp/table.tmp.json`')
			raise e
		os.remove(os.path.join('tmp', 'table.json'))
	elif suf == '.py':
		def merge_ver(table):
			ret = [row for row in table]
			last = ret[-1]
			for i in range(len(table) - 2, 0, -1):
				for j in range(len(last)):
					if last[j] == ret[i][j]:
						last[j] = None
				last = ret[i]
			return ret
		code = 'def render(context, options, merge_ver):\n'
		code += '\tglobal val\n'
		code += '\tfor key, val in context.items():\n'
		code += '\t\texec(\'%s = val\' % key, globals())\n'
		for line in open(common.pjoin('tmp', 'table.py'), 'rb'):
			code += '\t' + line.decode('utf-8').rstrip() + '\n'
		namespace = {}
		exec(code, namespace)
		table = json.loads(json.dumps(namespace['render'](context, options, merge_ver)))
	cnt = [[1] * len(row) for row in table]
	max_len = len(table[-1])
	for i in range(len(table) - 2, -1, -1):
		max_len = max(max_len, len(table[i]))
		for j in range(min(len(table[i]), len(table[i + 1]))):
			if table[i + 1][j] == None:
				cnt[i][j] += cnt[i + 1][j]
	ret = get_template(temp, context['prob'].lang()).render(context, table = table, cnt = cnt, width = max_len, options = options)
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
	common.check_install('gettext')
	def render(conf, contest, path):
		tex_problems = []
		day_name = conf['name'] if conf.folder == 'day' else '测试'
		probs = list(conf.probs())
		if len(probs) == 0:
			log.info('Nothing to do for %s' % conf.route)
			return
		for prob in probs:
			log.info(u'渲染题目题面 %s %s' % (comp, prob.route))
			try:
				shutil.copy(prob.statement(), common.pjoin('tmp', 'problem.md.jinja'))
			except common.NoFileException as e:
				log.error(u'找不到题面文件，建议使用`python -m generator problem`生成题目工程。')
				continue
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
				'json' : json
			}
			open(os.path.join('tmp', 'problem.md'), 'wb') \
				.write(get_template('problem_base.md.jinja', prob.lang())
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
			res = get_template('problem.tex.jinja', prob.lang()).render(
				context,
				template = lambda temp_name, **context : get_template(temp_name + '.tex.jinja', prob.lang()).render(context),
				table = lambda name, options = {} : table(os.path.join(prob.path, 'tables'), name, 'table.tex.jinja', context, options)
			)
			tex_problems.append(res)
				
		log.info(u'渲染比赛日题面 %s %s' % (comp, conf.route))
		context.pop('prob')
		context.pop('file_name')
		context.pop('down_file')
		context.pop('resource')
		context.pop('render')
		context['probs'] = list(conf.probs())
		context['problems'] = tex_problems
		all_problem_statement = get_template('%s.tex.jinja' % base_template).render(context)
		try:
			open(os.path.join('tmp', 'problems.tex'), 'wb') \
				.write(all_problem_statement.encode('utf-8'))
		except Exception as e:
			log.info(u'渲染出错的文件为`tmp/problems.tmp.tex`')
			open(os.path.join('tmp', 'problems.tmp.tex'), 'wb') \
				.write(all_problem_statement.encode('utf-8'))
			raise e
		log.info(u'开始使用xelatex渲染题面。')
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
			.write(get_template('zh-cn.md').render(context, conf = common.conf).encode('utf-8'))
		os.system('pandoc %s -t latex -o %s' % (
			os.path.join('tmp', 'precautions.md'),
			os.path.join('tmp', 'precautions.tex')
		))
		prec = open(os.path.join('tmp', 'precautions.tex'), 'rb').read().decode('utf-8')
	if common.conf.folder != 'problem':
		for day in common.days():
			result_path = os.path.join('statements', comp, day['name'] + ('-' + common.lang if common.lang else '') + '.pdf')
			render(day, common.conf if common.conf.folder == 'contest' else None, result_path)
	else:
		result_path = os.path.join('statements', comp, common.conf['name'] + ('-' + common.lang if common.lang else '') + '.pdf')
		render(common.conf, None, result_path)

def html(comp):
	def render(prob):
		log.info(u'渲染题目题面 %s %s' % (comp, prob.route))
		path = os.path.join('statements', comp, prob.route)
		if os.path.exists(os.path.join(prob.path, 'resources')):
			shutil.rmtree(path, ignore_errors = True)
			time.sleep(0.1)
			shutil.copytree(os.path.join(prob.path, 'resources'), path)
		try:
			shutil.copy(prob.statement(), common.pjoin('tmp', 'problem.md.jinja'))
		except common.NoFileException as e:
			log.error(u'找不到题面文件，建议使用`python -m generator problem`生成题目工程。')
			return
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
			'comp' : comp,
			'json' : json
		}
		open(os.path.join('tmp', 'problem.md'), 'wb') \
			.write(get_template('problem_base.md.jinja', prob.lang())
				.render(context)
				.encode('utf-8')
			)
		result_file = path + ('-' + common.lang if common.lang else '') + '.md'
		open(result_file, 'wb') \
			.write(get_template('problem.md', prob.lang())
				.render(
					context,
					template = lambda temp_name, **context : get_template(temp_name + '.html.jinja', prob.lang()).render(context),
					table = lambda name, options={} : table(os.path.join(prob.path, 'tables'), name, 'table.html.jinja', context, options)
				).encode('utf-8')
			)
		if common.start_file:
			common.xopen_file(result_file)

	common.mkdir(os.path.join('statements', comp))
	io_style = io_styles[comp]
	if common.conf.folder == 'contest':
		for day in common.days():
			if not os.path.exists(common.pjoin('statements', comp, day.route)):
				os.makedirs(common.pjoin('statements', comp, day.route))
	for prob in common.probs():
		render(prob)

if __name__ == '__main__':
	try:
		if common.init():
			common.check_install('jinja2')
			init()
			for common.work in common.works:
				for common.lang in common.langs:
					common.run_exc(work_list[common.work])
			final()
		else:
			log.info(u'支持的工作：%s' % ','.join(work_list.keys()))
	except common.NoFileException as e:
		log.error(e)
		log.info(u'尝试使用`python -m generator -h`获取如何生成一个工程。')
