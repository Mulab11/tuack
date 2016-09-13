# -*- coding: utf-8 -*-

from math import *
import json

def int_lg(num):
	if num == 0:
		return float('-inf')
	if num < 0:
		return float('nan')
	if num >= 10:
		if type(num) == int:
			return int_lg(num // 10) + 1
		else:
			return int_lg(num / 10) + 1
	if num < 1:
		return int_lg(num * 10) - 1
	return 0

def comma(num):
	if type(num) != int:
		return str(num)
	if num < 0:
		return '-' + comma(-num)
	if num < 1000:
		return str(num)
	return comma(num // 1000) + ',' + '%03d' % (num % 1000)
	
def hn(num):
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
			tmp = str(num / 10 ** n)
			ret += tmp
			l += len(tmp)
		ret += ' \\times '
		l += 1
	ret += '10^{%d}' % n
	l += 2 + len(str(n))
	return neg + (comma(num) if l >= len(str(num)) * 4 // 3 else ret)
	
def js_hn(num):
	return hn(num).replace('\\', '\\\\')
