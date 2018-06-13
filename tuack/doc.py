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

vars_re = r"\{%-? *do *vars\.__setitem__\( *'sample_id' *, *(\d+) *\) -%\}"

title_choices = {
	'sample' : {
		u'样例(\\d+)?',
		u'输入输出样例(\\d+)?',
		u'样例输入输出(\\d+)?',
		u'测试用例(\\d+)?',
		r'sample\s*(\d+)?',
		vars_re
	},
	'sample input' : {
		u'样例(\\d+)?输入(\\d+)?',
		u'输入(\\d+)?样例(\\d+)?',
		r'sample\s*input\s*(\d+)?',
		r'input\s*sample\s*(\d+)?'
	},
	'sample output' : {
		u'样例(\\d+)?输出(\\d+)?',
		u'输出(\\d+)?样例(\\d+)?',
		r'sample\s*output\s*(\d+)?',
		r'output\s*sample\s*(\d+)?'
	},
	'sample explanation' : {
		u'样例(\\d+)?说明(\\d+)?',
		u'样例(\\d+)?解释(\\d+)?',
		r'sample\s*explanation\s*(\d+)?'
	},
	'input' : {
		u'输入',
		'input'
	},
	'outout' : {
		u'输出',
		'output'
	},
	'explanation' : {
		u'解释',
		u'说明',
		'explanation'
	},
	'input format' : {
		u'输入格式',
		u'输入说明',
		u'输入要求',
		'input format'
	},
	'output format' : {
		u'输出格式',
		u'输出说明',
		u'输出要求',
		'output format'
	},
	'description' : {
		u'题目描述',
		u'题目说明',
		u'题目',
		u'问题描述',
		u'问题说明',
		u'问题',
		'description',
		'statement',
	},
	'background' : {
		u'题目背景',
		u'背景',
		'background',
	},
	'hint' : {
		u'提示',
		u'温馨提示',
		u'hint'
	},
	'subtasks' : {
		u'(数据规模|要求|限制|约束|约定|子任务)(与(数据规模|要求|限制|约束|约定|子任务))?',
		r'subtask(s?)'
	},
	'scoring' : {
		u'评分方式',
		'scoring'
	}
}

new_re_symbols = {
	r'\C' : '[\u4e00-\u9fbf]',
	r'\P' : '[\uff00-\uffef\u3000-\u303f\u2000-\u203f]'
}

text_patterns = {
	u'中文和英文、字符串或公式中间没有空格' : r'\C(?:\w|`|\$)',
	u'英文、字符串或公式和中文中间没有空格' : r'(?:\w|`|\$)\C',
	u'中文之间有空格' : r'\C \C',
	u'使用了英文标点或不在公式中的运算符号' : '[,\\.\\?\\:;\'"\\[\\]\\{\\}!\\\\\\|\\(\\)\\+=]'
}

title_re = re.compile('^(' + '|'.join(['|'.join(value) for value in title_choices.values()]) + ')$')
std_title_re = re.compile('^\{\{ *s\( *\'(.*)\' *(( *, *[-+.\'\"a-zA-Z0-9_ ]+)*)\) *\}\} *$')
doc_title_re = u'^#* *( *【|\{\{ *_ *\( *\')?(%s)(\' *\) *\}\}|】)?( *\{#.*\})? *#* *$'
html_equation_re = re.compile(r'\\\[(.*)\\\]\{\.math \.inline\}')
format_log_re = re.compile(r'^(\w) (\d+) (.*)$')

math_trans = {
	'*' : '',
	u'≤' : r' \le',
	u'≥' : r' \ge',
	u'←' : r' \leftarrow',
	u'→' : r' \rightarrow',
	u'×' : r' \times',
	u'∑' : r' \sum',
	r'\$' : ''
}

def is_digit(s):
	for c in s:
		if not '0' <= c <= '9':
			return False
	return True

def is_english(s):
	for c in s:
		if not('a' <= c <= 'z' and 'A' <= c <= 'Z'):
			return False
	return True

def is_chinese(s):
	for c in s:
		if not u'\u4e00' <= c <= u'\u9fbf':
			return False
	return True

def get_text(s):
	ret = ''
	for c in s:
		if is_chinese(c) or is_english(c) or is_digit(c):
			ret += c
	return ret.lower()
	
def html_math2tex_math(s):
	ret = ''
	i = 0
	l = len(s)
	in_sup = False
	in_sub = False
	while True:
		if i == l:
			break
		if i + 1 < l:
			flag = False
			if s[i:i+2] == '\*':
				ret += '*'
			elif s[i:i+2] == '\^':
				if in_sup:
					ret += ' }'
				else:
					ret += '^{ '
				in_sup ^= True
			elif s[i:i+2] == '\~':
				if in_sub:
					ret += ' }'
				else:
					ret += '_{ '
				in_sub ^= True
			elif s[i:i+2] in math_trans:
				ret += math_trans[s[i:i+2]]
			else:
				flag = True
			if not flag:
				i += 2
				continue
		if s[i] in math_trans:
			ret += math_trans[s[i]]
		else:
			ret += s[i]
		i += 1
	return ret

class Section:
	used = {'input' : 0, 'output' : 0}
	def __init__(self, name = None, args = None):
		self.name = name
		if args == None:
			self.args = []
		else:
			self.args = args
		self.lines = []
	def clear_paragraph(self):
		flag = True
		for idx, line in enumerate(self.lines):
			if idx % 2 == 1 and line.rstrip('\n\r') != '':
				flag = False
		if flag:
			self.lines = [line for idx, line in enumerate(self.lines) if idx % 2 == 0]
	def write(self, f, idx = None):
		if self.name == 'sample':
			if len(self.lines) == 0:
				return
			else:
				self.args.append('')
		for name, suf in [('input', '.in'), ('output', '.ans')]:
			if self.name == 'sample ' + name or self.name == name:
				self.used[name] += 1
				self.clear_paragraph()
				with open(pjoin(base.prob.path, 'down', str(self.used[name]) + suf), 'w') as ff:
					if len(self.lines) > 1 and self.lines[0].startswith('```'):
						lines = self.lines[1:-1]
					else:
						lines = self.lines
					for line in lines:
						ff.write(line + '\n')
				if name == 'input':
					f.write(b'{{ s(\'sample\', %d) }}\n\n{{ self.sample_text() }}\n\n' % self.used[name])
				return
		if idx == 0:
			f.write(b'{{ self.title() }}\n')
		if idx == 0 and self.name and self.name not in title_choices:
			base.prob['title'][base.prob.lang()] = self.name.strip()
		elif self.name:
			f.write(("\n{{ s('%s'%s) }}\n\n" % (
				self.name,
				', ' + ', '.join(map(json.dumps, self.args)) if len(self.args) > 0 else ''
			)).encode('utf-8'))
		for line in self.lines:
			f.write((line + '\n').encode('utf-8'))
	def is_empty(self):
		return not self.name and len(self.lines) == 0
	def format_line(self, line):
		ret = line
		while True:
			m = html_equation_re.search(ret)
			if not m:
				break
			while True:
				sm = m
				l, r = sm.span()
				sub = sm.string[l:r - 1]
				m = html_equation_re.search(sub)
				if m:
					continue
				sub = sm.string[l:r]
				res = sm.group(1)
				ret = ret.replace(sub, '$%s$' % html_math2tex_math(res))
				break
		return ret
	def format(self):
		self.lines = [self.format_line(line) for line in self.lines]

def sure_title(line):
	inp = line
	if inp.startswith('##'):
		return True
	if inp.startswith(u'【') and inp.endswith(u'】'):
		return True
	if std_title_re.match(inp):
		return True
	if re.match(vars_re, inp):
		return True
	txt = get_text(inp)
	if title_re.match(txt):
		return True
	return False

def get_title(line):
	m = std_title_re.match(line)
	if m:
		gps = m.groups()
		name = gps[0]
		args = json.loads('[' + ','.join(gps[1].split(',')[1:]) + ']')
		return name, args
	m = re.match(doc_title_re % '[-+.\'\"a-zA-Z0-9_ \u4e00-\u9fa5\u3040-\u309f\u30a0-\u30ff]+', line.lower())
	if m:
		title = m.group(2)
		m = title_re.match(title)
		if m:
			for key, pts in title_choices.items():
				for pt in pts:
					m = re.match('^' + pt + '$', title)
					if m:
						name = key
						args = []
						if key.startswith('sample'):
							for s in m.groups():
								if s and s != '':
									args = [json.loads(s)]
									log.debug(args)
									break
						return name, args
		return title, []
	return line, []

def to_sections(lines):
	def clear(buff):
		if buff != []:
			cur.lines.append(' '.join(buff))
			cur.lines.append('')
			buff = []
		return buff
	sections = []
	cur = Section()
	buff = []
	in_quote = False
	in_quote_space = False
	in_quote_tab = False
	in_equation = False
	in_table = False
	last_title = 0
	for line in lines:
		if in_quote_space:
			if line.startswith('    '):
				cur.lines.append(line.lstrip(' '))
				continue
			else:
				in_quote_space = False
				cur.lines.append('```')
		elif in_quote_tab:
			if line.startswith('\t'):
				cur.lines.append(line.lstrip(' '))
				continue
			else:
				in_quote_tab = False
				cur.lines.append('```')
		elif in_table:
			if line.startswith('  '):
				cur.lines.append(line)
				continue
			else:
				in_table = False
		if in_quote:
			if line == '```':
				in_quote = False
			cur.lines.append(line)
		elif in_equation:
			if line == '$$':
				in_quote = False
			cur.lines.append(line)
		else:
			last_title = last_title - 1 if last_title >= 1 else 0
			if line.startswith('```'):
				in_quote = True
				buff = clear(buff)
				cur.lines.append(line)
			elif line.strip() == '$$':
				in_equation = True
				buff = clear(buff)
				cur.lines.append(line)
			elif sure_title(line):
				buff = clear(buff)
				title, args = get_title(line)
				if not cur.is_empty():
					sections.append(cur)
				cur = Section(title, args)
				last_title = 2
			elif line.startswith('    '):
				in_quote_space = True
				buff = clear(buff)
				cur.lines.append('```')
				cur.lines.append(line.lstrip(' '))
			elif line.startswith('\t'):
				in_quote_space = True
				buff = clear(buff)
				cur.lines.append('```')
				cur.lines.append(line.lstrip(' '))
			elif line.startswith('  '):
				in_table = True
				buff = clear(buff)
				cur.lines.append(line)
			elif line.startswith('------'):
				if last_title >= 1:
					continue
				if buff != []:
					buff.pop()
				buff = clear(buff)
				title, args = get_title(last)
				if not cur.is_empty():
					sections.append(cur)
				cur = Section(title, args)
			elif line == '':
				buff = clear(buff)
			else:
				buff.append(line)
		last = line
	buff = clear(buff)
	if not cur.is_empty():
		sections.append(cur)
	return sections

def format():
	for base.prob in base.probs():
		prob = base.prob
		path = pjoin(base.conf.path, 'statement', base.conf.lang() + '.md')
		lines = [line.rstrip(b'\r\n').decode('utf-8') for line in open(path, 'rb').readlines()]
		sections = to_sections(lines)
		for section in sections:
			section.format()
		with open(path, 'wb') as f:
			for idx, section in enumerate(sections):
				section.write(f, idx)
	base.save_json(base.conf)

def format_check_one(path):
	log.info(u'检查文件`%s`。' % path)
	widths = [
		(126, 1), (159, 0), (687, 1), (710, 0), (711, 1), 
		(727, 0), (733, 1), (879, 0), (1154, 1), (1161, 0), 
		(4347, 1), (4447, 2), (7467, 1), (7521, 0), (8369, 1), 
		(8426, 0), (9000, 1), (9002, 2), (11021, 1), (12350, 2), 
		(12351, 1), (12438, 2), (12442, 0), (19893, 2), (19967, 1),
		(55203, 2), (63743, 1), (64106, 2), (65039, 1), (65059, 0),
		(65131, 2), (65279, 1), (65376, 2), (65500, 1), (65510, 2),
		(120831, 1), (262141, 2), (1114109, 1),
	]
	def get_width(o):
		if o == '\t':
			return 4
		o = ord(o)
		if o == 0xe or o == 0xf:
			return 0
		for num, wid in widths:
			if o <= num:
				return wid
		return 1
	def output():
		level = {
			'E' : log.error,
			'W' : log.warning,
			'I' : log.info,
			'D' : log.debug,
		}[logs[idx][0]]
		level(u'第%d行，第%d个字：%s' % (lineno, col, logs[idx][2]))
		lef = col - 10 if col > 10 else 0
		rig = min(lef + 21, len(code.rstrip()))
		log.info(code[lef:rig].replace('\u200b', '?').replace('\t', '    '))
		lef_cur = 0
		for c in code[:lef]:
			lef_cur += get_width(c)
		log.info(' ' * (cur - lef_cur) + u'↑')
	os.system('%s < %s > format.tmp 2> format.log' % (
		pjoin(base.tool_path, base.format_checker_name),
		path
	))
	tot = 0
	logs = []
	for line in open('format.log', 'rb'):
		m = format_log_re.match(line.decode('utf-8').rstrip())
		if m:
			logs.append((m.group(1), int(m.group(2)), m.group(3)))
	if len(logs) == 0:
		return
	idx = 0
	for lineno, line in enumerate(open(path, 'rb'), 1):
		code = line.decode('utf-8')
		cur = 0
		for col, ch in enumerate(code):
			tot += len(ch.encode('utf-8'))
			if tot >= logs[idx][1]:
				output()
				idx += 1
			if idx >= len(logs):
				return
			cur += get_width(ch)

def format_check():
	base.check_install('format')
	for base.prob in base.probs():
		prob = base.prob
		path = pjoin(prob.path, 'statement', 'zh-cn.md')
		format_check_one(path)

def load():
	if len(base.args) != 1:
		log.error(u'无法转换，必须传入恰好一个参数。')
		sys.exit(1)
	if base.conf.folder != 'problem':
		log.error(u'只能处理单个题目，请到题目目录下进行操作。')
		sys.exit(1)
	os.system('pandoc %s -o %s' % (base.args[0], pjoin(base.conf.path, 'statement', base.conf.lang() + '.md')))

class_list = {
	'load' : load,
	'format' : format,
	'check' : format_check
}

if __name__ == '__main__':
	try:
		if base.init():
			base.check_install('pandoc')
			base.check_install('jinja2')
			for base.work in base.works:
				for base.lang in base.langs:
					base.run_exc(class_list[base.work])
		else:
			log.info(u'这是用来处理题面的工具。')
			log.info(u'支持的工作：')
			log.info(u'  load     必须包含一个参数输入文件名，表示要导入的题面。')
			log.info(u'  format   尝试对当前的中文题面进行简单的格式化，危险操作请注意备份。')
			log.info(u'  check    对题面进行格式检查。')
			sys.exit(1)
	except base.NoFileException as e:
		log.error(e)
		log.info(u'尝试使用`python -m tuack.gen -h`获取如何生成一个工程。')
		sys.exit(1)

