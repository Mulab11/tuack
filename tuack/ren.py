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
from .base import log, pjoin
try:
	import jinja2
except:
	pass
from . import tools
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
	'ccc' : {'ccc-tex', 'ccc-md'},
	'ccc-tex' : {'ccc-tex'},
	'ccc-md' : {'ccc-md'},
	'tsinsen-oj' : {'tsinsen-oj'},
	'tex' : {'noi', 'ccpc', 'tupc', 'tuoi', 'ccc-tex'},
	'md' : {'uoj', 'tuoj', 'ccc-md'},
	'html' : {'tsinsen-oj'}
}
io_styles = {
	'noi' : 'fio',
	'ccpc' : 'stdio',
	'uoj' : 'stdio',
	'tuoj' : 'stdio',
	'ccc' : 'stdio',
	'tuoi' : 'stdio',
	'tupc' : 'stdio',
	'tsinsen-oj' : 'stdio'
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
	'uoj' : lambda : md('uoj'),
	'tupc' : lambda : tex('tupc'),
	'tuoi' : lambda : tex('tuoi'),
	'noi' : lambda : tex('noi'),
	'tuoj' : lambda : md('tuoj'),
	'ccc-tex' :  lambda : tex('ccc'),
	'ccc-md' : lambda : md('ccc'),
	'tsinsen-oj' : lambda : html('tsinsen-oj')
}

secondary_dict = {}
env = None

def get_template(fname, lang = None):
	global env
	if base.lang:
		lang = base.lang
	if not lang:
		lang = 'zh-cn'
	if env == None or base.system == 'Darwin' or (lang and env['lang'] != lang):
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
	base.mkdir('statements')
	shutil.rmtree('tmp', ignore_errors = True)
	time.sleep(0.1)
	shutil.copytree(os.path.join(base.path, 'templates'), 'tmp')
	
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
	if options == None:
		options = {}
	for suf in ['.py', '.json']:
		try:
			base.copy(path, name + suf, os.path.join('tmp', 'table' + suf))
			log.info(u'渲染表格`%s`，参数%s' % (base.pjoin(path, name + suf), str(options)))
			break
		except base.NoFileException as e:
			pass
	else:
		log.error(u'找不到表格`%s.*`' % base.pjoin(path, name))
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
		for line in open(base.pjoin('tmp', 'table.py'), 'rb'):
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
			if i in work_class and base.work in work_class[i]:
				in_set = True
				break
		if not in_set:
			return ''
	if work == 'tex' or work == 'html':
		id = str(uuid.uuid4())
		secondary_dict[id] = s
		return id
	else:
		return ' {{ ' + s + ' }} '

def to_arg(dic):
	return ','.join(['%s = %s' % (key, val if type(val) != str else json.dumps(val)) for key, val in dic.items()])

def tex(comp):
	base.check_install('pandoc')
	base.check_install('xelatex')
	base.check_install('gettext')
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
				shutil.copy(prob.statement(), base.pjoin('tmp', 'problem.md.jinja'))
			except base.NoFileException as e:
				log.error(u'找不到题面文件，建议使用`python -m generator problem`生成题目工程。')
				continue
			context = {
				'prob' : prob,
				'day' : conf if conf.folder == 'day' else None,
				'contest' : contest,
				'io_style' : io_style,
				'comp' : comp,
				'tools' : tools,
				'base' : base,
				'file_name' : lambda name : file_name(comp, prob, name),
				'down_file' : lambda name : open(os.path.join(prob.path, 'down', name), 'rb').read().decode('utf-8'),
				'resource' : lambda name : os.path.join('..', prob.path, 'resources', name).replace('\\', '/'),
				'render' : lambda s, sp = None : secondary(s, sp, 'tex'),
				'precautions' : prec,
				'json' : json
			}
			context['img'] = lambda src, env = None, **argw : context['render'](
				"template('image', resource = resource(%s), %s)" % (json.dumps(src), to_arg(argw)), 
				env
			)
			context['tbl'] = lambda src, env = None, **argw : context['render'](
				"table(%s, %s)" % (json.dumps(src), argw),
				env
			)
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
			tex = tex.replace('{{', '{ {').replace('}}', '} }').replace('{%', '{')	##强行修复pandoc搞出连续大括号与jinja冲突的问题
			for key, val in secondary_dict.items():
				tex = tex.replace(key, '{{ ' + val + ' }}')
			open(os.path.join('tmp', 'problem.tex.jinja'), 'wb').write(
				tex.encode('utf-8')
			)
			res = get_template('problem.tex.jinja', prob.lang()).render(
				context,
				template = lambda temp_name, **context : get_template(temp_name + '.tex.jinja', prob.lang()).render(context),
				table = lambda name, options = None : table(os.path.join(prob.path, 'tables'), name, 'table.tex.jinja', context, options)
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
		os.system('xelatex -interaction=batchmode problems.tex')
		os.system('xelatex -interaction=batchmode problems.tex')
		os.chdir('..')
		shutil.copy(os.path.join('tmp', 'problems.pdf'), path)
		if base.start_file:
			base.xopen_file(path)
	base.mkdir(os.path.join('statements', comp))
	io_style = io_styles[comp]
	base_template = base_templates[comp]
	context = {
		'io_style' : io_style,
		'comp' : comp,
		'tools' : tools,
		'base' : base,
		'json' : json
	}
	prec = None
	if os.path.exists(base.pjoin(base.conf.path, 'precautions', 'zh-cn.md')):
		base.copy(base.pjoin(base.conf.path, 'precautions'), 'zh-cn.md', 'tmp')
		open(base.pjoin('tmp', 'precautions.md'), 'wb') \
			.write(get_template('zh-cn.md').render(context, conf = base.conf).encode('utf-8'))
		os.system('pandoc %s -t latex -o %s' % (
			os.path.join('tmp', 'precautions.md'),
			os.path.join('tmp', 'precautions.tex')
		))
		prec = open(os.path.join('tmp', 'precautions.tex'), 'rb').read().decode('utf-8')
	if base.conf.folder != 'problem':
		for day in base.days():
			result_path = os.path.join('statements', comp, day['name'] + ('-' + base.lang if base.lang else '') + '.pdf')
			render(day, base.conf if base.conf.folder == 'contest' else None, result_path)
	else:
		result_path = os.path.join('statements', comp, base.conf['name'] + ('-' + base.lang if base.lang else '') + '.pdf')
		render(base.conf, None, result_path)

def uoj_title(text):
	in_quote = 0
	result = []
	for line in text.split(b'\n'):
		if in_quote == 0 and line.startswith(b'#'):
			result.append(b'#' + line)
		else:
			result.append(line)
		in_quote ^= line.count(b'```') & 1
	return b'\n'.join(result)

def md(comp):
	def render(prob):
		log.info(u'渲染题目题面 %s %s' % (comp, prob.route))
		path = pjoin('statements', comp)
		if prob.route != '':
			path = pjoin(path, prob.route)
		if os.path.exists(os.path.join(prob.path, 'resources')):
			shutil.rmtree(path, ignore_errors = True)
			time.sleep(0.1)
			shutil.copytree(os.path.join(prob.path, 'resources'), (path if prob.route != '' else pjoin(path, prob['name'])))
		try:
			shutil.copy(prob.statement(), base.pjoin('tmp', 'problem.md.jinja'))
		except base.NoFileException as e:
			log.error(u'找不到题面文件，建议使用`python -m tuack.gen problem`生成题目工程。')
			return
		time.sleep(0.1)
		context = {
			'prob' : prob,
			'io_style' : io_style,
			'tools' : tools,
			'base' : base,
			'file_name' : lambda name : file_name(comp, prob, name),
			'down_file' : lambda name : open(os.path.join(prob.path, 'down', name), 'rb').read().decode('utf-8'),
			'resource' : lambda name : prob['name'] + '/' + name,
			'render' : lambda s, sp = None : secondary(s, sp, 'md'),
			'comp' : comp,
			'json' : json
		}
		context['img'] = lambda src, env = None, **argw : context['render'](
			"template('image', resource = resource(%s), %s)" % (json.dumps(src), to_arg(argw)), 
			env
		)
		context['tbl'] = lambda src, env = None, **argw : context['render'](
			"table(%s, %s)" % (json.dumps(src), argw),
			env
		)
		open(os.path.join('tmp', 'problem.md'), 'wb') \
			.write(get_template('problem_base.md.jinja', prob.lang())
				.render(context)
				.encode('utf-8')
			)
		result_file = path + ('-' + base.lang if base.lang else '')
		if prob.route == '':
			result_file = pjoin(result_file, prob['name'])
		result_file += '.md'
		result_md = get_template('problem.md', prob.lang()).render(
			context,
			template = lambda temp_name, **context : get_template(temp_name + '.html.jinja', prob.lang()).render(context),
			table = lambda name, options = None : table(os.path.join(prob.path, 'tables'), name, 'table.html.jinja', context, options)
		).encode('utf-8')
		if comp == 'uoj':
			result_md = uoj_title(result_md)
		open(result_file, 'wb').write(result_md)
		if base.start_file:
			base.xopen_file(result_file)

	base.mkdir(os.path.join('statements', comp))
	io_style = io_styles[comp]
	if base.conf.folder == 'contest':
		for day in base.days():
			if not os.path.exists(base.pjoin('statements', comp, day.route)):
				os.makedirs(base.pjoin('statements', comp, day.route))
	for prob in base.probs():
		render(prob)
		
def html(comp):
	base.check_install('pandoc')
	def render(prob):
		log.info(u'渲染题目题面 %s %s' % (comp, prob.route))
		path = pjoin('statements', comp)
		if prob.route != '':
			path = pjoin(path, prob.route)
		if os.path.exists(os.path.join(prob.path, 'resources')):
			shutil.rmtree(path, ignore_errors = True)
			time.sleep(0.1)
			shutil.copytree(os.path.join(prob.path, 'resources'), (path if prob.route != '' else pjoin(path, prob['name'])))
		try:
			shutil.copy(prob.statement(), base.pjoin('tmp', 'problem.md.jinja'))
		except base.NoFileException as e:
			log.error(u'找不到题面文件，建议使用`python -m generator problem`生成题目工程。')
			return
		time.sleep(0.1)
		context = {
			'prob' : prob,
			'io_style' : io_style,
			'tools' : tools,
			'base' : base,
			'file_name' : lambda name : file_name(comp, prob, name),
			'down_file' : lambda name : open(os.path.join(prob.path, 'down', name), 'rb').read().decode('utf-8'),
			'resource' : lambda name : prob['name'] + '/' + name,
			'render' : lambda s, sp = None : secondary(s, sp, 'html'),
			'comp' : comp,
			'json' : json
		}
		context['img'] = lambda src, env = None, **argw : context['render'](
			"template('image', resource = resource(%s), %s)" % (json.dumps(src), to_arg(argw)), 
			env
		)
		context['tbl'] = lambda src, env = None, **argw : context['render'](
			"table(%s, %s)" % (json.dumps(src), argw),
			env
		)
		if comp == 'tsinsen-oj' and 'tsinsen_files' in dir(prob):
			context['resource'] = lambda name : '/RequireFile.do?fid=%s' % prob.tsinsen_files[name]
		open(os.path.join('tmp', 'problem.1.md'), 'wb') \
			.write(get_template('problem_base.md.jinja', prob.lang())
				.render(context)
				.encode('utf-8')
			)
		with open(os.path.join('tmp', 'problem.2.md'), 'wb') as f:
			for line in open(os.path.join('tmp', 'problem.1.md'), 'rb'):
				if re.match(b'^##[^#]', line):
					line = (u'## 【%s】\n' % line[2:].strip().decode('utf-8')).encode('utf-8')
				f.write(line)
		txt = open(os.path.join('tmp', 'problem.2.md'), 'rb').read().decode('utf-8')
		for key, val in secondary_dict.items():
			txt = txt.replace(key, '{{ ' + val + ' }}')
		open(os.path.join('tmp', 'problem.3.md'), 'wb').write(
			txt.encode('utf-8')
		)
		open(base.pjoin('tmp', 'problem.4.md'), 'wb') \
			.write(get_template('problem.3.md', prob.lang())
				.render(
					context,
					template = lambda temp_name, **context : get_template(temp_name + '.html.jinja', prob.lang()).render(context),
					table = lambda name, options = None : table(os.path.join(prob.path, 'tables'), name, 'table.html.jinja', context, options)
				).encode('utf-8')
			)
		result_file = path + ('-' + base.lang if base.lang else '')
		if prob.route == '':
			result_file = pjoin(result_file, prob['name'])
		result_file += '.html'
		os.system('pandoc %s -o %s' % (
			os.path.join('tmp', 'problem.4.md'),
			result_file
		))
		if base.start_file:
			base.xopen_file(result_file)

	base.mkdir(os.path.join('statements', comp))
	io_style = io_styles[comp]
	if base.conf.folder == 'contest':
		for day in base.days():
			if not os.path.exists(base.pjoin('statements', comp, day.route)):
				os.makedirs(base.pjoin('statements', comp, day.route))
	if comp == 'tsinsen-oj':
		log.warning(u'如果你使用了resource，你可能需要使用dumper才能获得正确上传清橙的文件。')
	for prob in base.probs():
		render(prob)

if __name__ == '__main__':
	try:
		if base.init():
			base.check_install('jinja2')
			init()
			for base.work in base.works:
				for base.lang in base.langs:
					base.run_exc(work_list[base.work])
			final()
		else:
			log.info(u'支持的工作：%s' % ','.join(sorted(work_list.keys())))
	except base.NoFileException as e:
		log.error(e)
		log.info(u'尝试使用`python -m generator -h`获取如何生成一个工程。')
