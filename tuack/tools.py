# -*- coding: utf-8 -*-

from datetime import *
from math import *
import sys
if sys.version_info >= (3, 0): 
	from builtins import *
else:
	from __builtin__ import *
import json
from .num2chinese import *
from .base import log

def int_lg(num):
	if num == 0:
		return float('-inf')
	if num < 0:
		return float('nan')
	if num >= 10:
		if issubclass(type(num), int):
			return int_lg(num // 10) + 1
		else:
			return int_lg(num / 10) + 1
	if num < 1:
		return int_lg(num * 10) - 1
	return 0

def comma(num):
	if not issubclass(type(num), int):
		return str(num)
	if num < 0:
		return '-' + comma(-num)
	if num < 1000:
		return str(num)
	return comma(num // 1000) + ',' + '%03d' % (num % 1000)
	
def hn(num, style = None):
	'''
	适合阅读的数
	'''
	ret = ''
	l = 0
	if num == 0:
		return '0'
	if num < 0:
		neg = '-'
		num = -num
	else:
		neg = ''
	n = int_lg(num)
	if num != 10 ** n:
		if num // 10 ** n * 10 ** n == num:
			ret += str(num // 10 ** n)
			l += 1
		else:
			tmp = str(float(num) / 10 ** n)
			ret += tmp
			l += len(tmp)
		ret += ' \\times '
		l += 1
	ret += '10^{%d}' % n
	l += 2 + len(str(n))
	if style == 'x':
		ret = ret
	elif style == ',':
		ret = comma(num)
	else:
		ret = (comma(num) if l >= len(str(num)) * 4 // 3 else ret)
	return neg + ret
	
def js_hn(num, style = None):
	'''
	适合阅读的数，json版本
	'''
	return json.dumps(hn(num, style))[1:-1]

def cases(cases):
	ret = []
	st = None
	ed = None
	def deal():
		if st is None:
			return
		if issubclass(type(st), int) and st + 1 < ed:
			ret.append("%d \\sim %d" % (st, ed))
		else:
			ret.append(str(st))
			if st != ed:
				ret.append(str(ed))
	for i in cases:
		if issubclass(type(st), int) and issubclass(type(i), int) and ed + 1 == i:
			ed = i
		else:
			deal()
			st = i
			ed = i
	deal()
	return '$' + ','.join(ret) + '$'

def to_time(dttm):
	try:
		return datetime.strptime(dttm, '%Y-%m-%d %H:%M:%S')
		#return datetime.strptime(dttm, '%Y-%m-%d %H:%M:%S%z')	#python2 兼容性不好，暂时不用时区了
	except Exception as e:
		return datetime.strptime(dttm[:-5], '%Y-%m-%d %H:%M:%S')
	
def time_range(start, end, year = '-', month = '-', day = ''):
	st = datetime.strptime(start[:-5], '%Y-%m-%d %H:%M:%S')
	ed = datetime.strptime(end[:-5], '%Y-%m-%d %H:%M:%S')
	#st = datetime.strptime(start, '%Y-%m-%d %H:%M:%S%z')	#python2 兼容性不好，暂时不用时区了
	#ed = datetime.strptime(end, '%Y-%m-%d %H:%M:%S%z')
	ret = st.strftime('%Y%%sQAQ%m%%sQAQ%d%%s %H:%M').replace('QAQ0', '').replace('QAQ', '') % (year, month, day)
	if st.second:
		ret += ':%02d' % st.second
	ret += ' ~ '
	flag = False
	if flag or ed.year != st.year:
		flag = True
		ret += '%04d%s' % (ed.year, year)
	if flag or ed.month != st.month:
		flag = True
		ret += '%d%s' % (ed.month, month)
	if flag or ed.day != st.day:
		flag = True
		ret += '%d%s' % (ed.day, day)
	ret += ' %02d:%02d' % (ed.hour, ed.minute)
	if ed.second:
		ret += ':%02d' % ed.second
	return ret

def json_dumps_twice(s):
	return json.dumps(json.dumps(s))

class Int(int):
	def __new__(self, a):
		return super(Int, self).__new__(self, a)
	hn = lambda self, style = None: globals()['hn'](self, style)
	js_hn = lambda self, style = None: globals()['js_hn'](self, style)
	comma = lambda self: globals()['comma'](self)
	int_lg = lambda self: globals()['int_lg'](self)
	to_chinese = lambda self, big=False, simp=True, o=False, twoalt=False: num2chinese(self, big, simp, o, twoalt)

class Float(float):
	def __new__(self, a):
		return super(Float, self).__new__(self, a)
	hn = lambda self, style = None: globals()['hn'](self, style)
	js_hn = lambda self, style = None: globals()['js_hn'](self, style)
	comma = lambda self: globals()['comma'](self)
	int_lg = lambda self: globals()['int_lg'](self)
	to_chinese = lambda self, big=False, simp=True, o=False, twoalt=False: num2chinese(self, big, simp, o, twoalt)

class Args(object):
	def __init__(self, *data):
		self.data = data
	def get(self, key, d = None, skip_none = False):
		ret = []
		for i in self.data:
			if i is None:
				continue
			for j in (i if type(i) == list else [i]):
				v = j.get('args', {}).get(key)
				if not skip_none or v is not None:
					ret.append(v)
		return ret
	def keys(self):
		ky = set()
		for i in self.data:
			ky |= set(i.keys())
		return ky
	def __getitem__(self, key):
		return self.get(key)
	def sum(self, key, d = None):
		return sum(self.get(key, d, True))
	def min(self, key, d = None):
		return min(self.get(key, d, True))
	def max(self, key, d = None):
		return max(self.get(key, d, True))
	def prod(self, key, d = None):
		return prod(self.get(key, d, True))

a = Args
