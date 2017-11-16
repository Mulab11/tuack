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
from . import common
from .common import log

def lemon(conf = None):
	common.check_install('pyside')
	if not conf:
		if common.conf.folder == 'problem':
			raise Exception('Can\'t dump a single problem to lemon, try to dump a day or a contest.')
		common.remkdir('lemon')
		if common.conf.folder == 'day':
			lemon(common.conf)
		else:
			for day in common.days():
				os.makedirs(common.pjoin('lemon', day.route))
				lemon(day)
		return
	log.info(u'导出lemon工程：%s' % conf.route)
	os.makedirs(common.pjoin('lemon', conf.route, 'data'))
	os.makedirs(common.pjoin('lemon', conf.route, 'source'))
	jzp_magic = 0x20111127
	zlib_magic = 0x185E
	import zlib
	from PySide import QtCore
	obuff = QtCore.QByteArray()
	ost = QtCore.QDataStream(obuff, QtCore.QIODevice.WriteOnly)
	ost.writeQString(conf['name'])
	probs = list(conf.probs())
	ost.writeInt32(len(probs))
	for prob in probs:
		log.info(u'导出lemon题目：%s' % prob.route)
		ost.writeQString(common.tr(prob['title']))
		ost.writeQString(prob['name'])
		ost.writeQString(prob['name'] + '.in')
		ost.writeQString(prob['name'] + '.out')
		ost.writeBool(False)
		ost.writeBool(False)
		ost.writeInt32(1 if prob['type'] == 'answer' else 0)
		ost.writeInt32(1)		# Judge Type TODO: What if there is spj (code = 4)
		ost.writeQString('--ignore-space-change --text --brief')
		ost.writeInt32(3)		# real precision (float number error bound)
		ost.writeQString('')	# spj route TODO: What if there is spj
		ost.writeInt32(len([i for i in prob['compile'] if i in {'cpp', 'c', 'pas'}]))
		for key, val in prob['compile'].items():
			try:
				ost.writeQString({
					'cpp' : 'g++',
					'c' : 'gcc',
					'pas' : 'fpc'
				}[key])
				ost.writeQString(val)
			except:
				pass
		ost.writeQString('out')
		if 'packed' in prob and prob['packed']:
			ost.writeInt32(len(prob['data']))
			for datum in prob['data']:
				ost.writeInt32(datum['score'])
				ost.writeInt32((datum['time limit'] if 'time limit' in datum else conf['time limit']) * 1000)
				ost.writeInt32(datum.memory_limit().MB)
				tc = datum['cases']
				ost.writeInt32(len(tc))
				for c in tc:
					ost.writeQString(common.pjoin(prob['name'], str(c) + '.in'))
				ost.writeInt32(len(tc))
				for c in tc:
					ost.writeQString(common.pjoin(prob['name'], str(c) + '.ans'))
		else:
			score = 100. / len(prob.test_cases)
			ost.writeInt32(len(prob.test_cases))
			for c in prob.test_cases:
				ost.writeInt32(score)
				ost.writeInt32(prob['time limit'] * 1000)
				ost.writeInt32(prob.memory_limit().MB)
				ost.writeInt32(1)
				ost.writeQString(common.pjoin(prob['name'], str(c) + '.in'))
				ost.writeInt32(1)
				ost.writeQString(common.pjoin(prob['name'], str(c) + '.ans'))
		
		sp = list(prob.route.split('/'))
		target = ['lemon'] + sp[:-1] + ['data', sp[-1]]
		shutil.copytree(common.pjoin(prob.path, 'data'), common.pjoin(*target))
	
	compressed = QtCore.QByteArray(zlib.compress(str(obuff)))
	obuff = QtCore.QByteArray()
	ost = QtCore.QDataStream(obuff, QtCore.QIODevice.WriteOnly)
	ost.writeUInt32(zlib_magic)
	ost.writeRawData(str(compressed))
	file_ = QtCore.QFile(common.pjoin('lemon', conf.route, conf['name'] + '.cdf'))
	file_.open(QtCore.QIODevice.WriteOnly)
	ofs = QtCore.QDataStream(file_)
	ofs.writeUInt32(jzp_magic)
	ofs.writeUInt16(QtCore.qChecksum(str(obuff), len(obuff)))
	ofs.writeUInt32(len(obuff))
	ofs.writeRawData(str(obuff))
	file_.close()
	
	common.run_r(common.unix2dos, common.pjoin('lemon', conf.route, 'data'))
	
	if common.do_zip:
		import zipfile
		with zipfile.ZipFile(common.pjoin('lemon', conf.route) + '.zip', 'w') as z:
			common.run_r(lambda path : z.write(path), common.pjoin('lemon', conf.route))
	
	log.warning(u'目前SPJ的支持暂时还没有实现，有需要请手工配置。')
	log.warning(u'目前lemon的编译选项是写在注册表里的，暂时没有实现该功能，请手工配置。')
'''userlist = {}'''
def arbiter(conf = None,daynum = 0):
	def arbiter_info(info, filename):
		with open(filename,'wb') as ofile:
			for key, val in info.items():
				ofile.write(('%s%s\n' % (key, val)).encode('gbk'))
	if not conf:
		print('makedirs')
		common.remkdir('arbiter')
		os.makedirs(common.pjoin('arbiter','data'))
		os.makedirs(common.pjoin('arbiter','final'))
		os.makedirs(common.pjoin('arbiter','players'))
		os.makedirs(common.pjoin('arbiter','result'))
		os.makedirs(common.pjoin('arbiter','filter'))
		os.makedirs(common.pjoin('arbiter','tmp'))
		if common.conf.folder == 'problem':
			raise Exception('Can\'t dump a single problem to arbiter, try to dump a day or a contest.')
		if common.conf.folder == 'day':
			arbiter(common.days())
		else:
			for idx, day in enumerate(common.days(), start = 1):
				os.makedirs(common.pjoin('arbiter','players',day.route))
				os.makedirs(common.pjoin('arbiter','result',day.route))
				arbiter(day,idx)
			print('dos2unix')
			common.run_r(common.dos2unix, common.pjoin('arbiter', 'data'))
			shutil.copytree(common.pjoin('arbiter','data'),common.pjoin('arbiter','evaldata'))	#这里也不能直接copy，见下面的处理方式
			cfg = {}
			cfg['NAME='] = common.conf['name']
			cfg['DAYNUM='] = idx
			cfg['ENV='] = 'env.info'
			cfg['PLAYER='] = 'player.info'
			cfg['TEAM='] = 'team.info'
			cfg['MISC='] = 'misc.info'
			arbiter_info(cfg,common.pjoin('arbiter','setup.cfg'))
			team = {}
			arbiter_info(team,common.pjoin('arbiter','team.info'))
			'''arbiter_info(userlist,common.pjoin('arbiter','player.info'))'''
		return
	dayinfo = {}
	dayinfo['NAME='] = u'第'+str(daynum)+u'场'+u'--机试'
	dayinfo['PLAYERDIR='] = ''
	dayinfo['CASEDIR='] = ''
	dayinfo['BASESCORE='] = 0
	dayinfo['TASKNUM='] = len(conf['subdir'])
	arbiter_info(dayinfo,common.pjoin('arbiter',conf['name']+'.info'))
	for probnum, prob in enumerate(conf.sub, start = 1):
		print(prob['name'])
		probinfo = {}
		probinfo['TITLE='] = ''
		probinfo['NAME='] = prob['name']
		probinfo['RUN='] = ''
		probinfo['INFILESUFFIX='] = 'in'
		probinfo['ANSFILESUFFIX='] = 'ans'
		probinfo['PLUG='] = prob['name']+'_e'
		if prob['type'] == 'program':
			probinfo['TYPE='] = 'SOURCE'
		else:
			print(u'【警告】暂时只支持非交互式程序题。')
		probinfo['LIMIT='] = int(prob['time limit'])
		probinfo['MEMLIMITS='] = int(prob.memory_limit().MB)
		probinfo['SAMPLES='] = len(prob.test_cases)
		score_per_case = 100 // len(prob.test_cases)
		if score_per_case * len(prob.test_cases) != 100:
			print(u'【警告】满分不是100哦。')
		probinfo['CCL=c@gcc'] = ' -o %o %i ' + prob['compile']['c']
		probinfo['CCL=cpp@g++'] = ' -o %o %i ' + prob['compile']['cpp']
		probinfo['CCL=pas@fpc'] = ' %i ' + prob['compile']['pas']
		if 'packed' in prob and prob['packed']:
			raise Exception('Can\'t dump packed problem for arbiter.')
		for idx, case in enumerate(prob.test_cases, start = 1):
			'''print('copyfile %s'%common.pjoin(prob.path,'data',case+'.in'))'''
			shutil.copy(
				common.pjoin(prob.path,'data',str(case)+'.in'),
				common.pjoin('arbiter','data',prob['name']+str(idx)+'.in')
			)
			'''print('copyfile %s'%common.pjoin(prob.path,'data',case+'.ans'))'''
			shutil.copy(
				common.pjoin(prob.path,'data',str(case)+'.ans'),
				common.pjoin('arbiter','data',prob['name']+str(idx)+'.ans')
			)
			probinfo['MARK='+str(idx)+'@'] = str(int(score_per_case))
		'''for idx, userdir in enumerate(prob['users'],start = 1):
			for idx2, code in enumerate(prob['users'][userdir],start = 1):
				dirname = prob['name']+'-'+str(idx)+str(idx2)
				codename = userdir + code
				tmplist = prob['users'][userdir][code].split('/')
				codedir = common.pjoin(prob.path,*tmplist)
				os.makedirs(common.pjoin('arbiter','players',conf['name'],dirname,prob['name']))
				shutil.copy(codedir,common.pjoin('arbiter','players',conf['name'],dirname,prob['name']))
				userlist[dirname + '@'] =  codename'''
		shutil.copy(common.pjoin(common.path,'sample','arbiter_e'),common.pjoin('arbiter','filter',prob['name']+'_e'))
		arbiter_info(probinfo,common.pjoin('arbiter','task'+str(daynum)+'_'+str(probnum)+'.info'))

def down(conf = None):
	if not conf:
		conf = common.conf
		common.remkdir('down')
	if conf.folder == 'problem':
		raise Exception('Can\'t dump a single problem to arbiter, try to dump a day or a contest.')
	if conf.folder == 'contest':
		for idx, day in enumerate(common.days(), start = 1):
			os.makedirs(common.pjoin('down', day['name']))
			down(day)
		print('dos2unix')
		common.run_r(common.dos2unix, common.pjoin('down'))
		return
	for prob in conf.probs():
		print(prob.route)
		os.makedirs(common.pjoin('down', prob.route))
		for idx, case in enumerate(prob.sample_cases, start = 1):
			shutil.copy(
				common.pjoin(prob.path,'down',str(case)+'.in'),
				common.pjoin('down', prob.route, prob['name']+str(idx)+'.in')
			)
			shutil.copy(
				common.pjoin(prob.path,'down',str(case)+'.ans'),
				common.pjoin('down', prob.route, prob['name']+str(idx)+'.ans')
			)

'''def arbiter_info(info,filename):
	with open(filename, 'wb') as f:
		for k, v in info.items():
			f.write(('%s%s\n' % (k, v)).encode('gbk'))

def arbiter(conf = None,daynum = 0):
	if not conf:
		print('makedirs')
		common.remkdir('arbiter')
		os.makedirs(common.pjoin('arbiter','data'))
		os.makedirs(common.pjoin('arbiter','final'))
		os.makedirs(common.pjoin('arbiter','players'))
		os.makedirs(common.pjoin('arbiter','result'))
		os.makedirs(common.pjoin('arbiter','tmp'))
		if common.conf.folder == 'problem':
			raise Exception('Can\'t dump a single problem to arbiter, try to dump a day or a contest.')
		if common.conf.folder == 'day':
			arbiter(common.days())
		else:
			for day_num, day in enumerate(common.days(), start = 1):
				os.makedirs(common.pjoin('arbiter','players',day.route))
				os.makedirs(common.pjoin('arbiter','result',day.route))
				arbiter(day,daynum)
			print('dos2unix')
			common.run_r(common.dos2unix, common.pjoin('arbiter', 'data'))
			shutil.copytree(common.pjoin('arbiter','data'),common.pjoin('arbiter','evaldata'))
			cfg = {}
			cfg['NAME='] = common.conf['name']
			cfg['DAYNUM='] = daynum
			cfg['ENV='] = 'env.info'
			cfg['PLAYER='] = 'player.info'
			cfg['TEAM='] = 'team.info'
			cfg['MISC='] = 'misc.info'
			arbiter_info(cfg,common.pjoin('arbiter','setup.cfg'))
			team = {}
			arbiter_info(team,common.pjoin('arbiter','team.info'))
		return
	dayinfo = {}
	dayinfo['NAME='] = u'第'+str(daynum)+u'场'+u'——'+conf['name']
	dayinfo['PLAYERDIR='] = ''
	dayinfo['CASEDIR='] = ''
	dayinfo['BASESCORE='] = 0
	dayinfo['TASKNUM='] = len(conf['subdir'])
	arbiter_info(dayinfo,common.pjoin('arbiter',conf['name']+'.info'))
	probnum = 0
	for prob in common.probs(conf):
		probnum += 1
		print(prob['name'])
		probinfo = {}
		probinfo['TITLE='] = ''
		probinfo['NAME='] = prob['name']
		probinfo['RUN='] = ''
		probinfo['INFILESUFFIX='] = 'in'
		probinfo['ANSFILESUFFIX='] = 'ans'
		probinfo['PLUG='] = prob['name']+'_e'
		if prob['type'] == 'program':
			probinfo['TYPE='] = 'SOURCE'
		else:
			print(u'暂时只支持非交互式程序题')
		probinfo['LIMIT='] = int(prob['time limit'])
		probinfo['MEMLIMITS='] = int(prob.memory_limit().MB)
		probinfo['SAMPLES='] = len(prob.test_cases)
		score_per_case = 100 / len(prob.test_cases)
		probinfo['CLL=c@gcc'] = ' -o $o $i ' + prob['compile']['c']
		probinfo['CLL=cpp@g++'] = ' -o $o $i ' + prob['compile']['cpp']
		probinfo['CLL=pas@fpc'] = ' -o $o $i ' + prob['compile']['pas']
		if 'packed' in prob and prob['packed']:
			raise Exception('Can\'t dump packed problem for arbiter.')
		else:
			casenum = 0
			for case in prob.test_cases:
				shutil.copy(common.pjoin(prob.path,'data',str(case)+'.in'),common.pjoin('arbiter','data',prob['name']+case+'.in'))
				shutil.copy(common.pjoin(prob.path,'data',str(case)+'.ans'),common.pjoin('arbiter','data',prob['name']+case+'.ans'))
				casenum += 1
				probinfo['MARK='+str(casenum)+'@'] = score_per_case
			shutil.copy(common.pjoin(common.path,'sample','arbiter_e'),common.pjoin('arbiter','data',prob['name']+'_e'))
		arbiter_info(probinfo,common.pjoin('arbiter','task'+str(daynum)+'_'+str(probnum)+'.info'))
'''

def tsinsen_oj():
	import random
	if type(common.conf) != common.Problem:
		log.error(u'只能转换一道题目，请到相应题目目录下运行')
		return
	hash_ch = list(map(
		chr,
		[ord('a') + i for i in range(26)] + \
		[ord('A') + i for i in range(26)] + \
		[ord('0') + i for i in range(10)]
	))
	hash = lambda l = 10 : ''.join([hash_ch[random.randint(0, len(hash_ch) - 1)] for i in range(l)])
	if not os.path.exists('tsinsen-oj'):
		os.makedirs('tsinsen-oj')
	for day in common.days():
		p = common.pjoin('tsinsen-oj', day.route)
		if not os.path.exists(p):
			os.makedirs(p)
	for prob in common.probs():
		p = common.pjoin('tsinsen-oj', prob.route)
		if not os.path.exists(p):
			os.makedirs(p)
		if os.path.exists(common.pjoin(prob.path, 'down')):
			with zipfile.ZipFile(common.pjoin('tsinsen-oj', prob.route, 'down.zip'), 'w') as z:
				common.run_r(lambda path : z.write(path), common.pjoin(prob.path, 'down'))
			prob.tsinsen_down = hash(8)
		else:
			prob.tsinsen_down = None
		files = {}
		path = common.pjoin(prob.path, 'resources')
		if os.path.exists(path):
			common.run_r(lambda p : files.__setitem__(p[len(path) + 1:], hash(8)), path)
		prob.tsinsen_files = files
	if common.do_render:
		import renderer
		tmp = common.start_file
		common.start_file = False
		renderer.init()
		renderer.html('tsinsen-oj')
		renderer.final()
		common.start_file = tmp
	else:
		log.warning(u'如果你使用了文件，不重新渲染题面会导致tsinsen的文件失效。')
	
	read_file = lambda path : open(path, 'rb').read().decode('utf-8')
	
	Title = lambda : prob.tr('title')
	CheckPoint = lambda : prob['key words'] if 'key words' in prob else ''
	TestMethod = lambda : 'DEFAULT'
	InputFileName = lambda : ''
	OutputFileName = lambda : ''
	TimeLimit = lambda : '%.1fs' % prob['time limit']
	MemoryLimit = lambda : '%.1fMB' % prob.memory_limit().MB
	
	def Checkers():
		path = common.pjoin('data', 'chk', 'chk.cpp')
		if os.path.exists(path):
			return open(path, 'rb').read().decode('utf-8')
		else:
			return '\n'
	def Description():
		path = common.pjoin('statements', 'tsinsen-oj', prob.route + '.html')
		if not os.path.exists(path):
			log.warning(u'找不到题面，你可能需要自己手工添加题面。')
			return ''
		header = u'<p>下载目录：<img src="/RequireFile.do?fid=%s" alt="另存为图片下载" />（另存为图片下载）</p>\n' % prob.tsinsen_down
		return header + read_file(path)
	def Solution():
		for user, codes in prob['users'].items():
			for name, path in codes.items():
				if name.startswith('std') or name.endswith('std') or name.endswith('std.cpp'):
					return read_file(path)
		for user, codes in prob['users'].items():
			for name, path in codes.items():
				return read_file(path)
		return ''
	def add_shell(name, func):
		h = hash()
		ret = '%s=\n' % name
		ret += '======================%s\n' % h
		res = func()
		if not res.endswith('\n'):
			res += '\n'
		ret += res
		ret += '======================%s\n' % h
		return ret.encode('utf-8')
	def to_base64(path):
		import base64
		s = base64.b64encode(open(path, 'rb').read()).decode('utf-8')
		return '\n'.join(s[pos:pos+76] for pos in range(0, len(s), 76))
	tokens = [
		'Title', 'CheckPoint', 'Checkers', 'TestMethod', 'Description',
		'InputFileName', 'OutputFileName', 'Solution', 'TimeLimit', 'MemoryLimit'
	]
	for prob in common.probs():
		result_file = common.pjoin('tsinsen-oj', prob.route) + '.txt'
		with open(result_file, 'wb') as f:
			for token in tokens:
				f.write(add_shell(token, eval(token)))
			if prob['packed']:
				log.warning(u'清橙OJ不支持打包评测和指定测试点分值，直接将所有测试点视为相同。')
			for datum in prob.test_cases:
				f.write(add_shell('InData', lambda : read_file(common.pjoin('data', datum + '.in'))))
				f.write(add_shell('OutData', lambda : read_file(common.pjoin('data', datum + '.ans'))))
			if prob.tsinsen_down:
				f.write(add_shell('FileName', lambda : 'down.zip'))
				f.write(add_shell('File(%s)' % prob.tsinsen_down, lambda : to_base64(common.pjoin('tsinsen-oj', prob.route, 'down.zip'))))
			for key, val in prob.tsinsen_files.items():
				f.write(add_shell('FileName', lambda : key.replace('/', '-').replace('\\', '-')))
				f.write(add_shell('File(%s)' % val, lambda : to_base64(common.pjoin(prob.path, 'resources', key))))
		if common.start_file:
			common.xopen_file(result_file)

work_list = {
	'lemon' : lemon,
	'arbiter' : arbiter,
	'down' : down,
	'tsinsen-oj' : tsinsen_oj
}

if __name__ == '__main__':
	try:
		if common.init():
			for common.work in common.works:
				common.run_exc(work_list[common.work])
		else:
			log.info(u'这个工具用于导出成其他类型的工程。')
			log.info(u'支持的工作：%s' % ','.join(work_list.keys()))
	except common.NoFileException as e:
		log.error(e)
		log.info(u'尝试使用`python -m generator -h`获取如何生成一个工程。')
