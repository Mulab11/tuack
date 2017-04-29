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

def lemon(conf = None):
	common.check_install('pyside')
	if not conf:
		if common.conf['folder'] == 'problem':
			raise Exception('Can\'t dump a single problem to lemon, try to dump a day or a contest.')
		common.remkdir('lemon')
		if common.conf['folder'] == 'day':
			lemon(common.conf)
		else:
			for day in common.days():
				os.makedirs(common.pjoin('lemon', day['route']))
				lemon(day)
		return
	os.makedirs(common.pjoin('lemon', conf['route'], 'data'))
	os.makedirs(common.pjoin('lemon', conf['route'], 'source'))
	jzp_magic = 0x20111127
	zlib_magic = 0x185E
	import zlib
	from PySide import QtCore
	obuff = QtCore.QByteArray()
	ost = QtCore.QDataStream(obuff, QtCore.QIODevice.WriteOnly)
	ost.writeQString(conf['name'])
	ost.writeInt32(len(conf['sub']))
	for prob in common.probs(conf):
		ost.writeQString(common.default_lang(prob['title']))
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
		ost.writeInt32(len(prob['compile']))
		for key, val in prob['compile'].items():
			ost.writeQString({
				'cpp' : 'g++',
				'c' : 'gcc',
				'pas' : 'fpc'
			}[key])
			ost.writeQString(val)
		ost.writeQString('out')
		if 'packed' in prob and prob['packed']:
			ost.writeInt32(len(prob['data']))
			for datum in prob['data']:
				ost.writeInt32(datum['score'])
				ost.writeInt32((datum['time limit'] if 'time limit' in datum else conf['time limit']) * 1000)
				ost.writeInt32(common.memory2bytes(datum['memory limit'] if 'memory limit' in datum else conf['memory limit']) / 2 ** 20)
				tc = datum['cases']
				ost.writeInt32(len(tc))
				for c in tc:
					ost.writeQString(common.pjoin(prob['name'], str(c) + '.in'))
				ost.writeInt32(len(tc))
				for c in tc:
					ost.writeQString(common.pjoin(prob['name'], str(c) + '.ans'))
		else:
			score = 100. / len(prob['test cases'])
			ost.writeInt32(len(prob['test cases']))
			for c in prob['test cases']:
				ost.writeInt32(score)
				ost.writeInt32(prob['time limit'] * 1000)
				ost.writeInt32(common.memory2bytes(prob['memory limit']) / 2 ** 20)
				ost.writeInt32(1)
				ost.writeQString(common.pjoin(prob['name'], str(c) + '.in'))
				ost.writeInt32(1)
				ost.writeQString(common.pjoin(prob['name'], str(c) + '.ans'))
		
		sp = list(prob['route'].split('/'))
		target = ['lemon'] + sp[:-1] + ['data', sp[-1]]
		shutil.copytree(common.pjoin(prob['path'], 'data'), common.pjoin(*target))
	
	compressed = QtCore.QByteArray(zlib.compress(str(obuff)))
	obuff = QtCore.QByteArray()
	ost = QtCore.QDataStream(obuff, QtCore.QIODevice.WriteOnly)
	ost.writeUInt32(zlib_magic)
	ost.writeRawData(str(compressed))
	file_ = QtCore.QFile(common.pjoin('lemon', conf['route'], conf['name'] + '.cdf'))
	file_.open(QtCore.QIODevice.WriteOnly)
	ofs = QtCore.QDataStream(file_)
	ofs.writeUInt32(jzp_magic)
	ofs.writeUInt16(QtCore.qChecksum(str(obuff), len(obuff)))
	ofs.writeUInt32(len(obuff))
	ofs.writeRawData(str(obuff))
	file_.close()
	
	common.run_r(common.unix2dos, common.pjoin('lemon', conf['route'], 'data'))
	
	if common.do_zip:
		import zipfile
		with zipfile.ZipFile(common.pjoin('lemon', conf['route']) + '.zip', 'w') as z:
			common.run_r(lambda path : z.write(path), common.pjoin('lemon', conf['route']))
	
	print(u'【警告】目前SPJ的支持暂时还没有实现，有需要请手工配置。')
	print(u'【警告】目前lemon的编译选项是写在注册表里的，暂时没有实现该功能，请手工配置。')
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
		if common.conf['folder'] == 'problem':
			raise Exception('Can\'t dump a single problem to arbiter, try to dump a day or a contest.')
		if common.conf['folder'] == 'day':
			arbiter(common.days())
		else:
			for idx, day in enumerate(common.days(), start = 1):
				os.makedirs(common.pjoin('arbiter','players',day['route']))
				os.makedirs(common.pjoin('arbiter','result',day['route']))
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
	dayinfo['NAME='] = '第'+str(daynum)+'场'+'--机试'
	dayinfo['PLAYERDIR='] = ''
	dayinfo['CASEDIR='] = ''
	dayinfo['BASESCORE='] = 0
	dayinfo['TASKNUM='] = len(conf['subdir'])
	arbiter_info(dayinfo,common.pjoin('arbiter',conf['name']+'.info'))
	for probnum, prob in enumerate(common.probs(conf), start = 1):
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
		probinfo['MEMLIMITS='] = int(common.memory2bytes(prob['memory limit'])/(2**20))
		probinfo['SAMPLES='] = len(prob['test cases'])
		score_per_case = 100 // len(prob['test cases'])
		if score_per_case * len(prob['test cases']) != 100:
			print(u'【警告】满分不是100哦。')
		probinfo['CCL=c@gcc'] = ' -o %o %i ' + prob['compile']['c']
		probinfo['CCL=cpp@g++'] = ' -o %o %i ' + prob['compile']['cpp']
		probinfo['CCL=pas@fpc'] = ' %i ' + prob['compile']['pas']
		if 'packed' in prob and prob['packed']:
			raise Exception('Can\'t dump packed problem for arbiter.')
		for idx, case in enumerate(prob['test cases'], start = 1):
			'''print('copyfile %s'%common.pjoin(prob['path'],'data',case+'.in'))'''
			shutil.copy(
				common.pjoin(prob['path'],'data',str(case)+'.in'),
				common.pjoin('arbiter','data',prob['name']+str(idx)+'.in')
			)
			'''print('copyfile %s'%common.pjoin(prob['path'],'data',case+'.ans'))'''
			shutil.copy(
				common.pjoin(prob['path'],'data',str(case)+'.ans'),
				common.pjoin('arbiter','data',prob['name']+str(idx)+'.ans')
			)
			probinfo['MARK='+str(idx)+'@'] = str(int(score_per_case))
		'''for idx, userdir in enumerate(prob['users'],start = 1):
			for idx2, code in enumerate(prob['users'][userdir],start = 1):
				dirname = prob['name']+'-'+str(idx)+str(idx2)
				codename = userdir + code
				tmplist = prob['users'][userdir][code].split('/')
				codedir = common.pjoin(prob['path'],*tmplist)
				os.makedirs(common.pjoin('arbiter','players',conf['name'],dirname,prob['name']))
				shutil.copy(codedir,common.pjoin('arbiter','players',conf['name'],dirname,prob['name']))
				userlist[dirname + '@'] =  codename'''
		shutil.copy(common.pjoin(common.path,'sample','standard_e'),common.pjoin('arbiter','filter',prob['name']+'_e'))
		arbiter_info(probinfo,common.pjoin('arbiter','task'+str(daynum)+'_'+str(probnum)+'.info'))

def down(conf = None):
	if not conf:
		common.remkdir('down')
		if common.conf['folder'] == 'problem':
			raise Exception('Can\'t dump a single problem to arbiter, try to dump a day or a contest.')
		if common.conf['folder'] == 'day':
			down(common.days())
		else:
			for idx, day in enumerate(common.days(), start = 1):
				down(day)
			print('dos2unix')
			common.run_r(common.dos2unix, common.pjoin('down'))
		return
	os.makedirs(common.pjoin('down',conf['name']))
	for prob in common.probs(conf):
		print(prob['name'])
		os.makedirs(common.pjoin('down',conf['name'],prob['name']))
		for idx, case in enumerate(prob['sample cases'], start = 1):
			shutil.copy(
				common.pjoin(prob['path'],'down',str(case)+'.in'),
				common.pjoin('down',conf['name'],prob['name'],prob['name']+str(idx)+'.in')
			)
			shutil.copy(
				common.pjoin(prob['path'],'down',str(case)+'.ans'),
				common.pjoin('down',conf['name'],prob['name'],prob['name']+str(idx)+'.ans')
			)

work_list = {
	'lemon' : lemon,
	'arbiter' : arbiter,
	'down' : down
}

if __name__ == '__main__':
	if common.init():
		common.infom('Dumping starts at %s.\n' % str(datetime.datetime.now()))
		for common.work in common.works:
			work_list[common.work]()
	else:
		pass
