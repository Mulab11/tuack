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

def table(path, name, temp, context, options):
	if options == None:
		options = {}
	for suf in ['.py', '.pyinc', '.json']:
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
	elif suf == '.py' or suf == '.pyinc':
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
		for line in open(base.pjoin('tmp', 'table' + suf), 'rb'):
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

def to_arg(dic):
	return ','.join(['%s = %s' % (key, val if type(val) != str else json.dumps(val)) for key, val in dic.items()])

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

class Base(object):
	def __init__(self, comp, conf = None):
		self.conf = (base.conf if conf == None else conf)
		self.comp = comp
		self.day = None
		self.contest = None
		self.prob = None
		self.path = None
		self.prec = None
		self.secondary_dict = {}
		self.io_style = io_styles[comp]

	def file_name(self, name):
		if self.comp == 'noi':
			return self.prob['name'] + '/' + name
		elif self.comp == 'uoj':
			return name
		else:
			return name

	def secondary(self, s, sp = None):
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
		if self.work == 'tex' or self.work == 'html':
			id = str(uuid.uuid4())
			self.secondary_dict[id] = s
			return id
		else:
			return ' {{ ' + s + ' }} '

	def resource(self, name):
		return self.prob['name'] + '/' + name

	def ren_prob_md_j(self):
		log.info(u'渲染题目题面 %s %s' % (self.comp, self.prob.route))
		try:
			shutil.copy(self.prob.statement(), pjoin('tmp', 'problem.md.jinja'))
			time.sleep(0.1)
		except base.NoFileException as e:
			log.error(u'找不到题面文件，建议使用`python -m tuack.gen problem`生成题目工程。')
			return
		self.context = {
			'prob' : self.prob,
			'args' : self.prob.get('args'),
			'data' : self.prob.get('data'),
			'samples' : self.prob.get('samples'),
			'pre' : self.prob.get('pre'),
			'day' : self.day,
			'contest' : self.contest,
			'io_style' : self.io_style,
			'comp' : self.comp,
			'tools' : tools,
			'tl' : tools,
			'base' : base,
			'file_name' : self.file_name,
			'down_file' : lambda name : open(os.path.join(self.prob.path, 'down', name), 'rb').read().decode('utf-8'),
			'resource' : self.resource,
			'render' : self.secondary,
			'precautions' : self.prec,
			'json' : json
		}
		self.context['img'] = lambda src, env = None, **argw : self.context['render'](
			"template('image', resource = resource(%s), %s)" % (json.dumps(src), to_arg(argw)),
			env
		)
		self.context['tbl'] = lambda src, env = None, **argw : self.context['render'](
			"table(%s, %s)" % (json.dumps(src), argw),
			env
		)
		if self.comp == 'tsinsen-oj' and 'tsinsen_files' in dir(self.prob):
			self.context['resource'] = lambda name : '/RequireFile.do?fid=%s' % self.prob.tsinsen_files[name]
		open(os.path.join('tmp', 'problem.md'), 'wb') \
			.write(get_template('problem_base.md.jinja', self.prob.lang())
				.render(self.context)
				.encode('utf-8')
			)
		time.sleep(0.1)

	def check_install(self):
		pass

	def before(self):
		base.mkdir('statements')
		shutil.rmtree('tmp', ignore_errors = True)
		time.sleep(0.1)
		shutil.copytree(os.path.join(base.path, 'templates'), 'tmp')
		base.mkdir(pjoin('statements', self.comp))
		if self.conf.folder == 'contest':
			self.contest = self.conf
		elif self.conf.folder == 'day':
			self.day = self.conf
		elif self.conf.folder == 'problem':
			self.prob = self.conf

	def move_resource(self):
		if os.path.exists(os.path.join(self.prob.path, 'resources')):
			shutil.rmtree(self.path, ignore_errors = True)
			time.sleep(0.1)
			shutil.copytree(os.path.join(self.prob.path, 'resources'), (self.path if self.prob.route != '' else pjoin(self.path, self.prob['name'])))

	def gen_paths(self):
		self.path = pjoin('statements', self.comp)
		if self.prob.route != '':
			self.path = pjoin(self.path, self.prob.route)
		self.result_path = self.path + ('-' + base.lang if base.lang else '')
		if self.prob.route == '':
			self.result_path = pjoin(self.result_path, self.prob['name'])
		self.result_path += '.' + self.work

	def main(self):
		if self.conf.folder == 'contest':
			for self.day in self.conf.days():
				if not os.path.exists(pjoin('statements', self.comp, self.day.route)):
					os.makedirs(pjoin('statements', self.comp, self.day.route))
		if self.comp == 'tsinsen-oj':
			log.warning(u'如果你使用了resource，你可能需要使用dumper才能获得正确上传清橙的文件。')
		for self.prob in self.conf.probs():
			self.gen_paths()
			self.move_resource()
			self.ren_prob_md_j()
			self.ren_prob_rest()
			self.start_file()

	def final(self):
		shutil.rmtree('tmp', ignore_errors = True)

	def run(self):
		self.check_install()
		self.before()
		self.main()
		self.final()

	def start_file(self):
		if base.start_file:
			base.xopen_file(self.result_path)

class Latex(Base):
	work = 'tex'
	day_templates = {
		'noi' : 'tuoi',
		'tuoi' : 'tuoi',
		'tupc' : 'tupc',
		'ccpc' : 'ccpc',
		'ccc' : 'ccc'
	}

	def resource(self, name):
		return pjoin('..', self.prob.path, 'resources', name).replace('\\', '/')

	def check_install(self):
		base.check_install('pandoc')
		base.check_install('xelatex')
		base.check_install('gettext')

	def ren_prec(self):
		if not os.path.exists(base.pjoin(self.conf.path, 'precautions', 'zh-cn.md')):
			return
		context = {
			'io_style' : self.io_style,
			'comp' : self.comp,
			'tools' : tools,
			'tl' : tools,
			'base' : base,
			'json' : json
		}
		base.copy(base.pjoin(self.conf.path, 'precautions'), 'zh-cn.md', 'tmp')
		open(base.pjoin('tmp', 'precautions.md'), 'wb') \
			.write(get_template('zh-cn.md').render(context, conf = self.conf).encode('utf-8'))
		os.system('pandoc %s -t latex -o %s' % (
			os.path.join('tmp', 'precautions.md'),
			os.path.join('tmp', 'precautions.tex')
		))
		prec = open(os.path.join('tmp', 'precautions.tex'), 'rb').read().decode('utf-8')

	@staticmethod
	def repair_jinja_bracket(text):
		return text.replace('{{', '{ {').replace('}}', '} }').replace('{%', '{')

	def ren_prob_tex(self):
		os.system('pandoc %s -t latex -o %s' % (
			pjoin('tmp', 'problem.md'),
			pjoin('tmp', 'problem.tex')
		))
		tex = open(os.path.join('tmp', 'problem.tex'), 'rb').read().decode('utf-8')
		tex = self.repair_jinja_bracket(tex)	##强行修复pandoc搞出连续大括号与jinja冲突的问题
		for key, val in self.secondary_dict.items():
			tex = tex.replace(key, '{{ ' + val + ' }}')
		open(os.path.join('tmp', 'problem.tex.jinja'), 'wb').write(
			tex.encode('utf-8')
		)
		return get_template('problem.tex.jinja', self.prob.lang()).render(
			self.context,
			template = lambda temp_name, **context : get_template(temp_name + '.tex.jinja', self.prob.lang()).render(context),
			table = lambda name, options = None : table(os.path.join(self.prob.path, 'tables'), name, 'table.tex.jinja', self.context, options)
		)

	def ren_day_pdf(self):
		log.info(u'渲染比赛日题面 %s %s' % (self.comp, self.day.route if self.day else self.conf.route))
		self.context.pop('prob')
		self.context.pop('file_name')
		self.context.pop('down_file')
		self.context.pop('resource')
		self.context.pop('render')
		self.context['probs'] = self.probs
		self.context['problems'] = self.tex_problems
		all_problem_statement = get_template('%s.tex.jinja' % base_templates[self.comp]).render(self.context)
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
		shutil.copy(os.path.join('tmp', 'problems.pdf'), self.result_path)

	def ren_day(self):
		if self.day:
			day_name = self.day['name']
			self.probs = list(self.day.probs())
		else:
			day_name = u'测试'
			self.probs = [self.prob]
		if len(self.probs) == 0:
			log.info(u'指定目录`%s`下没有题目可渲染。' % conf.route)
			return
		self.tex_problems = []
		for self.prob in self.probs:
			self.ren_prob_md_j()
			self.tex_problems.append(self.ren_prob_tex())
		self.ren_day_pdf()
		self.start_file()

	def main(self):
		self.ren_prec()
		self.day_template = self.day_templates[self.comp]
		if self.conf.folder != 'problem':
			for self.day in base.days():
				self.result_path = os.path.join('statements', self.comp, self.day.name_lang() + '.pdf')
				self.ren_day()
		else:
			self.result_path = os.path.join('statements', self.comp, self.conf.name_lang() + '.pdf')
			self.ren_day()

class Markdown(Base):
	work = 'md'
	def ren_prob_rest(self):
		result_md = get_template('problem.md', self.prob.lang()).render(
			self.context,
			template = lambda temp_name, **context : get_template(temp_name + '.html.jinja', self.prob.lang()).render(context),
			table = lambda name, options = None : table(os.path.join(self.prob.path, 'tables'), name, 'table.html.jinja', self.context, options)
		).encode('utf-8')
		if self.comp == 'uoj':
			result_md = uoj_title(result_md)
		open(self.result_path, 'wb').write(result_md)

class Html(Base):
	work = 'html'
	def check_install(self):
		base.check_install('pandoc')

	def ren_prob_rest(self):
		if self.comp == 'tsinsen-oj':
			with open(os.path.join('tmp', 'problem.2.md'), 'wb') as f:
				for line in open(os.path.join('tmp', 'problem.md'), 'rb'):
					if re.match(b'^##[^#]', line):
						line = (u'## 【%s】\n' % line[2:].strip().decode('utf-8')).encode('utf-8')
					f.write(line)
		else:
			base.copy('tmp', 'problem.md', pjoin('tmp', 'problem.2.md'))
		txt = open(os.path.join('tmp', 'problem.2.md'), 'rb').read().decode('utf-8')
		for key, val in self.secondary_dict.items():
			txt = txt.replace(key, '{{ ' + val + ' }}')
		open(os.path.join('tmp', 'problem.3.md'), 'wb').write(
			txt.encode('utf-8')
		)
		open(base.pjoin('tmp', 'problem.4.md'), 'wb') \
			.write(get_template('problem.3.md', self.prob.lang())
				.render(
					self.context,
					template = lambda temp_name, **context : get_template(temp_name + '.html.jinja', self.prob.lang()).render(context),
					table = lambda name, options = None : table(os.path.join(self.prob.path, 'tables'), name, 'table.html.jinja', self.context, options)
				).encode('utf-8')
			)
		os.system('pandoc %s -o %s' % (
			os.path.join('tmp', 'problem.4.md'),
			self.result_path
		))

class_list = {
	'ccpc' : Latex,
	'uoj' : Markdown,
	'tupc' : Latex,
	'tuoi' : Latex,
	'noi' : Latex,
	'tuoj' : Markdown,
	'ccc-tex' : Latex,
	'ccc-md' : Markdown,
	'tsinsen-oj' : Html
}

comp_list = {
	'ccpc' : 'ccpc',
	'uoj' : 'uoj',
	'tupc' : 'tupc',
	'tuoi' : 'tuoi',
	'noi' : 'noi',
	'tuoj' : 'tuoj',
	'ccc-tex' : 'ccc',
	'ccc-md' : 'ccc',
	'tsinsen-oj' : 'tsinsen-oj'
}

if __name__ == '__main__':
	try:
		if base.init():
			base.check_install('jinja2')
			for base.work in base.works:
				for base.lang in base.langs:
					base.run_exc(class_list[base.work](comp_list[base.work]).run)
		else:
			log.info(u'支持的工作：%s' % ','.join(sorted(class_list.keys())))
	except base.NoFileException as e:
		log.error(e)
		log.info(u'尝试使用`python -m tuack.gen -h`获取如何生成一个工程。')