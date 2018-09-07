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
import gettext
from . import base
from .base import log, pjoin
try:
	import jinja2
except:
	pass
from . import tools
import uuid
import traceback

work_class = {
	'noi' : {'noi'},
	'ccpc' : {'ccpc'},
	'uoj' : {'uoj'},
	'tupc' : {'tupc'},
	'tuoj-pc' : {'tupc', 'tuoj'},
	'tuoi' : {'tuoi'},
	'tuoj-oi' : {'tuoi', 'tuoj'},
	'tuoj' : {'tuoj'},
	'thuoj' : {'thuoj'},
	'ccc' : {'ccc-tex', 'ccc-md'},
	'ccc-tex' : {'ccc-tex'},
	'ccc-md' : {'ccc-md'},
	'tsinsen-oj' : {'tsinsen-oj'},
	'tex' : {'noi', 'ccpc', 'tupc', 'tuoi', 'ccc-tex'},
	'md' : {'uoj', 'tuoj', 'ccc-md', 'loj'},
	'html' : {'tsinsen-oj'},
	'doku' : {'thuoj'}
}
io_styles = {
	'noi' : 'fio',
	'ccpc' : 'stdio',
	'uoj' : 'stdio',
	'tuoj' : 'stdio',
	'ccc' : 'stdio',
	'tuoi' : 'stdio',
	'tupc' : 'stdio',
	'tsinsen-oj' : 'stdio',
	'loj' : 'stdio',
	'thuoj' : 'stdio'
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
pandoc_version = None

def detect_pandoc_version():
	global pandoc_version
	if pandoc_version is not None:
		return
	cp = subprocess.Popen(['pandoc', '-v'], stdout = subprocess.PIPE)
	line = cp.stdout.read().decode().splitlines()[0]
	pandoc_version = line.split()[-1]

def get_pandoc_option():
	detect_pandoc_version()
	if pandoc_version.startswith('2.'):
		option = '-f markdown-smart -t latex-smart'
	else:
		option = '--no-tex-ligatures -t latex'
	return option

def get_template(fname, lang = None):
	global env
	if base.lang:
		lang = base.lang
	if not lang:
		lang = 'zh-cn'
	if env == None or base.system == 'Darwin' or (lang and env['lang'] != lang):
		env = {
			'env' : jinja2.Environment(
				loader = jinja2.FileSystemLoader(pjoin(os.getcwd(), 'tmp')),
				extensions = ['jinja2.ext.do', 'jinja2.ext.with_', 'jinja2.ext.i18n']
			),
			'lang' : lang
		}
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
			base.copy(path, name + suf, pjoin('tmp', 'table' + suf))
			log.info(u'渲染表格`%s`，参数%s' % (base.pjoin(path, name + suf), str(options)))
			break
		except base.NoFileException as e:
			pass
	else:
		raise base.NoFileException(u'找不到表格`%s.*`' % base.pjoin(path, name))
	if suf == '.json':
		res = get_template('table.json', context['prob'].lang()).render(context, options = options)
		try:
			table = json.loads(res)
		except Exception as e:
			open(pjoin('tmp', 'table.tmp.json'), 'w').write(res)
			log.error(u'json文件错误`tmp/table.tmp.json`')
			raise e
		os.remove(pjoin('tmp', 'table.json'))
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
		try:
			table = json.loads(json.dumps(namespace['render'](context, options, merge_ver)))
		except Exception as e:
			log.error(e)
			lines = traceback.format_exc().splitlines()
			for idx, line in enumerate(lines):
				if '<string>' in line:
					m = re.match(r'^.*line (\d*),.*$', line)
					if m:
						lineno = int(m.group(1)) - 4
						log.info('  File "%s", line %d' % (base.pjoin(path, name + suf), lineno))
						log.info(code.splitlines()[lineno + 3][1:])
						for i in range(idx + 1, len(lines)):
							log.info(lines[i])
						break
			else:
				raise e
			raise e
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

def uoj_title(text):	## 很显然，这个是在瞎整，不过UOJ为什么从二级标题开始用？修改标题字体大小应该改CSS而不是题目嘛
	in_quote = 0
	result = []
	for line in text.split(b'\n'):
		if in_quote == 0 and line.startswith(b'#'):
			result.append(b'#' + line)
		else:
			result.append(line)
		in_quote ^= line.count(b'```') & 1
	return b'\n'.join(result)
	
def loj_bug(text):		## 学弟也学着我瞎整，伤心QAQ
	# TODO: Avoid duplication
	in_quote = 0
	result = []
	for line in text.split(b'\n'):
		if in_quote == 0 and line.startswith(b'<table'):
			result.append(line
				.replace(b'$<', b'$ <')   # LOJ Markdown 渲染的已知 bug
			)
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
		if self.work == 'tex' or self.work == 'html' or self.work == 'doku':
			id = str(uuid.uuid4())
			self.secondary_dict[id] = s
			return id
		else:
			return ' {{ ' + s + ' }} '

	def resource(self, name):
		return self.prob['name'] + '/' + name
		
	def down_file(self, name):
		ret = ''
		fname = pjoin(self.prob.path, 'down', name)
		length_warned = False
		for idx, line in enumerate(open(fname, 'rb')):
			if len(line) > 60 and not length_warned:
				log.warning(u'文件`%s`的第%d行太长，建议只提供下发而不渲染到题面。' % (fname, idx + 1))
				length_warned = True
			ret += line.decode('utf-8')
		return ret
		
	def titlize(self, title, args, lang = None):
		if base.lang:
			lang = base.lang
		if not lang:
			lang = 'zh-cn'
		if title == 'sample':
			if len(args) > 0:
				self.context['vars']['sample_id'] = args[0]
			if len(args) <= 1:
				return ''
		tra = gettext.translation('lang', os.getcwd() + '/tmp', [env['lang']])
		ret = tra.gettext(title)
		if len(args) > 0:
			try:
				ret = ret % args
			except Exception as e:
				ret = ret + ''.join(map(str, args))
		else:
			try:
				ret = ret % ('',)
			except Exception as e:
				pass
		return '## ' + ret

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
			'dargs' : tools.a(self.prob.get('data')),
			'pargs' : tools.a(self.prob.get('pre')),
			'sargs' : tools.a(self.prob.get('samples')),
			'aargs' : tools.a(self.prob.get('data'), self.prob.get('pre'), self.prob.get('samples')),
			'day' : self.day,
			'contest' : self.contest,
			'io_style' : self.io_style,
			'comp' : self.comp,
			'tools' : tools,
			'tl' : tools,
			'base' : base,
			'common' : base,
			'file_name' : self.file_name,
			'down_file' : self.down_file,
			'resource' : self.resource,
			'render' : self.secondary,
			'precautions' : self.prec,
			'json' : json,
			'vars' : {},
			's' : lambda title, *args : self.titlize(title, args, self.prob.lang())
		}
		self.context['img'] = lambda src, env = None, **argw : self.context['render'](
			"template('image', resource = resource(%s), %s)" % (json.dumps(src), to_arg(argw)),
			env
		)
		self.context['font'] = lambda txt, env = None, **argw : self.context['render'](
			"template('font', txt = %s, %s)" % (json.dumps(txt), to_arg(argw)),
			env
		)
		self.context['tbl'] = lambda src, env = None, **argw : self.context['render'](
			"table(%s, %s)" % (json.dumps(src), argw),
			env
		)
		if self.comp == 'tsinsen-oj' and 'tsinsen_files' in dir(self.prob):
			self.context['resource'] = lambda name : '/RequireFile.do?fid=%s' % self.prob.tsinsen_files[name]
		open(pjoin('tmp', 'problem.md'), 'wb') \
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
		shutil.copytree(pjoin(base.path, 'templates'), 'tmp')
		base.mkdir(pjoin('statements', self.comp))
		if self.conf.folder == 'contest':
			self.contest = self.conf
		elif self.conf.folder == 'day':
			self.day = self.conf
		elif self.conf.folder == 'problem':
			self.prob = self.conf

	def move_resource(self):
		if os.path.exists(pjoin(self.prob.path, 'resources')):
			shutil.rmtree(self.path, ignore_errors = True)
			time.sleep(0.1)
			shutil.copytree(pjoin(self.prob.path, 'resources'), (self.path if self.prob.route != '' else pjoin(self.path, self.prob['name'])))

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
		os.system('pandoc %s %s -o %s' % (
			get_pandoc_option(),
			pjoin('tmp', 'precautions.md'),
			pjoin('tmp', 'precautions.tex')
		))
		self.prec = open(pjoin('tmp', 'precautions.tex'), 'rb').read().decode('utf-8')

	def ren_prob_tex(self):
		os.system('pandoc %s %s -o %s' % (
			get_pandoc_option(),
			pjoin('tmp', 'problem.md'),
			pjoin('tmp', 'problem.tex')
		))
		tex = open(pjoin('tmp', 'problem.tex'), 'rb').read().decode('utf-8')
		for key, val in self.secondary_dict.items():	## 如果未来发生了性能问题，这里可以先写到一个文件里然后再解析
			open(pjoin('tmp', key + '.tex.jinja'), 'wb').write(
				('{{ ' + val + ' }}').encode('utf-8')
			)
			ret = get_template(key + '.tex.jinja', self.prob.lang()).render(
				self.context,
				template = lambda temp_name, **context : get_template(temp_name + '.tex.jinja', self.prob.lang()).render(context),
				table = lambda name, options = None : table(pjoin(self.prob.path, 'tables'), name, 'table.tex.jinja', self.context, options)
			)
			tex = tex.replace(key, ret)
		self.secondary_dict = {}
		return tex

	def gen_compile(self):
		clangs = {l for prob in self.probs for l in prob.get('compile', {}).keys()}
		ret = {}
		for clang in clangs:
			cur = []
			for prob in self.probs:
				if prob['type'] != 'output':
					if clang in prob['compile']:
						cur.append({
							'option' : prob['compile'][clang] + (' -Wl,--stack=%d' % prob.memory_limit().B if clang in {'cpp', 'c'} and base.out_system == 'Windows' else ''),
							'cnt' : 1,
							'use' : True
						})
					else:
						cur.append({'option' : u'不可用', 'cnt' : 1, 'use' : False})
				else:
					cur.append({'option' : 'N/A', 'cnt' : 1, 'use' : False})
			last = []
			for p in cur:
				if len(last) == 0 or p['option'] != last[-1]['option']:
					last.append(p)
				else:
					last[-1]['cnt'] += 1
			ret[clang] = last
		return ret

	def ren_day_pdf(self):
		log.info(u'渲染比赛日题面 %s %s' % (self.comp, self.day.route if self.day else self.conf.route))
		self.context.pop('prob')
		self.context.pop('file_name')
		self.context.pop('down_file')
		self.context.pop('resource')
		self.context.pop('render')
		self.context['probs'] = self.probs
		self.context['problems'] = self.tex_problems
		self.context['compile'] = self.gen_compile()
		all_problem_statement = get_template('%s.tex.jinja' % base_templates[self.comp]).render(self.context)
		try:
			open(pjoin('tmp', 'problems.tex'), 'wb') \
				.write(all_problem_statement.encode('utf-8'))
		except Exception as e:
			log.info(u'渲染出错的文件为`tmp/problems.tmp.tex`')
			open(pjoin('tmp', 'problems.tmp.tex'), 'wb') \
				.write(all_problem_statement.encode('utf-8'))
			raise e
		log.info(u'开始使用xelatex渲染题面。')
		os.chdir('tmp')
		os.system('xelatex -interaction=batchmode problems.tex')
		os.system('xelatex -interaction=batchmode problems.tex')
		if not os.path.exists('problems.pdf'):
			log.warning(u'题面渲染失败，尝试使用关闭静默模式渲染。')
			os.system('xelatex problems.tex')
			os.system('xelatex problems.tex')
		if not os.path.exists('problems.pdf'):
			log.error(u'题面渲染失败，请检查`tmp`目录下各文件。')
		os.chdir('..')
		shutil.copy(pjoin('tmp', 'problems.pdf'), self.result_path)

	def ren_day(self):
		if self.day:
			day_name = self.day['name']
			self.probs = list(self.day.probs())
		else:
			day_name = u'测试'
			self.probs = [self.prob]
		if len(self.probs) == 0:
			log.info(u'指定目录`%s`下没有题目可渲染。' % (self.day.path if self.day else self.conf.path))
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
				self.result_path = pjoin('statements', self.comp, self.day.name_lang() + '.pdf')
				self.ren_day()
		else:
			self.result_path = pjoin('statements', self.comp, self.conf.name_lang() + '.pdf')
			self.ren_day()

class Markdown(Base):
	work = 'md'
	def ren_prob_rest(self):
		result_md = get_template('problem.md', self.prob.lang()).render(
			self.context,
			template = lambda temp_name, **context : get_template(temp_name + '.html.jinja', self.prob.lang()).render(context),
			table = lambda name, options = None : table(pjoin(self.prob.path, 'tables'), name, 'table.html.jinja', self.context, options)
		).encode('utf-8')
		if self.comp == 'uoj':
			result_md = uoj_title(result_md)
		elif self.comp == 'loj':
			result_md = loj_bug(result_md)
		open(self.result_path, 'wb').write(result_md)

class Html(Base):
	work = 'html'
	def check_install(self):
		base.check_install('pandoc')

	def ren_prob_rest(self):
		if self.comp == 'tsinsen-oj':
			with open(pjoin('tmp', 'problem.2.md'), 'wb') as f:
				for line in open(pjoin('tmp', 'problem.md'), 'rb'):
					if re.match(b'^##[^#]', line):
						line = (u'## 【%s】\n' % line[2:].strip().decode('utf-8')).encode('utf-8')
					f.write(line)
		else:
			base.copy('tmp', 'problem.md', pjoin('tmp', 'problem.2.md'))
		txt = open(pjoin('tmp', 'problem.2.md'), 'rb').read().decode('utf-8')
		for key, val in self.secondary_dict.items():
			txt = txt.replace(key, '{{ ' + val + ' }}')
		open(pjoin('tmp', 'problem.3.md'), 'wb').write(
			txt.encode('utf-8')
		)
		open(base.pjoin('tmp', 'problem.4.md'), 'wb') \
			.write(get_template('problem.3.md', self.prob.lang())
				.render(
					self.context,
					template = lambda temp_name, **context : get_template(temp_name + '.html.jinja', self.prob.lang()).render(context),
					table = lambda name, options = None : table(pjoin(self.prob.path, 'tables'), name, 'table.html.jinja', self.context, options)
				).encode('utf-8')
			)
		os.system('pandoc %s -o %s' % (
			pjoin('tmp', 'problem.4.md'),
			self.result_path
		))

class DoKuWiki(Base):
	work = 'doku'
	def check_install(self):
		base.check_install('pandoc')

	def ren_prob_rest(self):
		os.system('pandoc %s -o %s -w dokuwiki' % (
			pjoin('tmp', 'problem.md'),
			pjoin('tmp', 'problem.doku')
		))
		txt = open(pjoin('tmp', 'problem.doku'), 'rb').read().decode('utf-8')
		for key, val in self.secondary_dict.items():
			txt = txt.replace(key, '{{ ' + val + ' }}')
		open(pjoin('tmp', 'problem.2.doku'), 'wb').write(
			txt.encode('utf-8')
		)
		open(self.result_path, 'wb') \
			.write(get_template('problem.2.doku', self.prob.lang())
				.render(
					self.context,
					template = lambda temp_name, **context : '<HTML>' + get_template(temp_name + '.html.jinja', self.prob.lang()).render(context) + '</HTML>',
					table = lambda name, options = None : '<HTML>' + table(pjoin(self.prob.path, 'tables'), name, 'table.html.jinja', self.context, options).strip() + '</HTML>'
				).encode('utf-8')
			)

class_list = {
	'ccpc' : Latex,
	'uoj' : Markdown,
	'tupc' : Latex,
	'tuoi' : Latex,
	'noi' : Latex,
	'tuoj' : Markdown,
	'ccc-tex' : Latex,
	'ccc-md' : Markdown,
	'tsinsen-oj' : Html,
	'loj' : Markdown,
	'thuoj' : DoKuWiki
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
	'tsinsen-oj' : 'tsinsen-oj',
	'loj' : 'loj',
	'thuoj' : 'thuoj'
}

if __name__ == '__main__':
	try:
		if base.init():
			base.check_install('jinja2')
			for base.work in base.works:
				for base.lang in base.langs:
					base.run_exc(class_list[base.work](comp_list[base.work]).run)
		else:
			log.info(u'这个工具用于渲染题面。')
			log.info(u'支持的工作：%s' % ','.join(sorted(class_list.keys())))
	except base.NoFileException as e:
		log.error(e)
		log.info(u'尝试使用`python -m tuack.gen -h`获取如何生成一个工程。')
