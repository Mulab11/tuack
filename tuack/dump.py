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
import requests
import traceback
from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor

def lemon(conf = None):
	base.check_install('pyside')
	if not conf:
		if base.conf.folder == 'problem':
			raise Exception('Can\'t dump a single problem to lemon, try to dump a day or a contest.')
		base.remkdir('lemon')
		if base.conf.folder == 'day':
			lemon(base.conf)
		else:
			for day in base.days():
				os.makedirs(base.pjoin('lemon', day.route))
				lemon(day)
		return
	log.info(u'导出lemon工程：%s' % conf.route)
	os.makedirs(base.pjoin('lemon', conf.route, 'data'))
	os.makedirs(base.pjoin('lemon', conf.route, 'source'))
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
		ost.writeQString(base.tr(prob['title']))
		ost.writeQString(prob['name'])
		ost.writeQString(prob['name'] + '.in')
		ost.writeQString(prob['name'] + '.out')
		ost.writeBool(False)
		ost.writeBool(False)
		ost.writeInt32(1 if prob['type'] == 'output' else 0)
		ost.writeInt32(1)		# Judge Type TODO: What if there is spj (code = 4)
		ost.writeQString('--ignore-space-change --text --brief')
		ost.writeInt32(3)		# real precision (float number error bound)
		ost.writeQString('')	# spj route TODO: What if there is spj
		ost.writeInt32(len([i for i in prob.get('compile', {}) if i in {'cpp', 'c', 'pas'}]))
		for key, val in prob.get('compile', {}).items():
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
		if prob.packed:
			ost.writeInt32(len(prob['data']))
			for datum in prob['data']:
				ost.writeInt32(datum['score'])
				ost.writeInt32(datum.get('time limit', prob.get('time limit', 0)) * 1000)
				ost.writeInt32(base.Memory(datum.get('memory limit', prob.get('memory limit', '0 B'))).MB)
				tc = datum['cases']
				ost.writeInt32(len(tc))
				for c in tc:
					ost.writeQString(base.pjoin(prob['name'], str(c) + '.in'))
				ost.writeInt32(len(tc))
				for c in tc:
					ost.writeQString(base.pjoin(prob['name'], str(c) + '.ans'))
		else:
			score = (100. / len(prob.test_cases) if len(prob.test_cases) > 0 else 0.)
			ost.writeInt32(len(prob.test_cases))
			for c in prob.test_cases:
				ost.writeInt32(score)
				ost.writeInt32(prob['time limit'] * 1000)
				ost.writeInt32(prob.memory_limit().MB)
				ost.writeInt32(1)
				ost.writeQString(base.pjoin(prob['name'], str(c) + '.in'))
				ost.writeInt32(1)
				ost.writeQString(base.pjoin(prob['name'], str(c) + '.ans'))
		
		sp = list(prob.route.split('/'))
		target = ['lemon'] + sp[:-1] + ['data', sp[-1]]
		shutil.copytree(base.pjoin(prob.path, 'data'), base.pjoin(*target))
	
	compressed = QtCore.QByteArray(zlib.compress(str(obuff)))
	obuff = QtCore.QByteArray()
	ost = QtCore.QDataStream(obuff, QtCore.QIODevice.WriteOnly)
	ost.writeUInt32(zlib_magic)
	ost.writeRawData(str(compressed))
	file_ = QtCore.QFile(base.pjoin('lemon', conf.route, conf['name'] + '.cdf'))
	file_.open(QtCore.QIODevice.WriteOnly)
	ofs = QtCore.QDataStream(file_)
	ofs.writeUInt32(jzp_magic)
	ofs.writeUInt16(QtCore.qChecksum(str(obuff), len(obuff)))
	ofs.writeUInt32(len(obuff))
	ofs.writeRawData(str(obuff))
	file_.close()
	
	base.run_r(base.unix2dos, base.pjoin('lemon', conf.route, 'data'))
	
	if base.do_zip:
		import zipfile
		with zipfile.ZipFile(base.pjoin('lemon', conf.route) + '.zip', 'w') as z:
			base.run_r(lambda path : z.write(path), base.pjoin('lemon', conf.route))
	log.warning(u'目前SPJ的支持暂时还没有实现，有需要请手工配置。')
	log.warning(u'目前lemon的编译选项是写在注册表里的，暂时没有实现该功能，请手工配置。')

def arbiter_main(conf = None,daynum = 0):
	def arbiter_info(info, filename):
		with open(filename,'wb') as ofile:
			for key, val in info.items():
				ofile.write(('%s%s\n' % (key, val)).encode('gbk'))
	if not conf:
		log.info('makedirs')
		if not os.path.exists('arbiter'):
			base.remkdir('arbiter')
		base.remkdir(pjoin('arbiter', 'main'))
		os.makedirs(base.pjoin('arbiter', 'main','data'))
		os.makedirs(base.pjoin('arbiter', 'main','final'))
		os.makedirs(base.pjoin('arbiter', 'main','players'))
		os.makedirs(base.pjoin('arbiter', 'main','result'))
		os.makedirs(base.pjoin('arbiter', 'main','filter'))
		os.makedirs(base.pjoin('arbiter', 'main','tmp'))
		if base.conf.folder == 'problem':
			raise Exception('Can\'t dump a single problem to arbiter, try to dump a day or a contest.')
		if base.conf.folder == 'day':
			arbiter(base.days())
		else:
			for idx, day in enumerate(base.days(), start = 1):
				os.makedirs(base.pjoin('arbiter', 'main','players','day%d' % idx))
				os.makedirs(base.pjoin('arbiter', 'main','result','day%d' % idx))
				arbiter_main(day,idx)
			log.info('dos2unix')
			base.run_r(base.dos2unix, base.pjoin('arbiter', 'main', 'data'))
			shutil.copytree(base.pjoin('arbiter', 'main','data'),base.pjoin('arbiter', 'main','evaldata'))	#这里也不能直接copy，见下面的处理方式
			cfg = {}
			cfg['NAME='] = base.conf['name']
			cfg['DAYNUM='] = idx
			cfg['ENV='] = 'env.info'
			cfg['PLAYER='] = 'player.info'
			cfg['TEAM='] = 'team.info'
			cfg['MISC='] = 'misc.info'
			arbiter_info(cfg,base.pjoin('arbiter', 'main','setup.cfg'))
			team = {}
			arbiter_info(team,base.pjoin('arbiter', 'main','team.info'))
			'''arbiter_info(userlist,base.pjoin('arbiter','player.info'))'''
		return
	dayinfo = {}
	dayinfo['NAME='] = u'第'+str(daynum)+u'场'+u'--机试'
	dayinfo['PLAYERDIR='] = ''
	dayinfo['CASEDIR='] = ''
	dayinfo['BASESCORE='] = 0
	dayinfo['TASKNUM='] = len(conf['subdir'])
	arbiter_info(dayinfo,base.pjoin('arbiter', 'main', 'day%d.info' % daynum))
	for probnum, prob in enumerate(conf.sub, start = 1):
		log.info(prob['name'])
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
			log.warning(u'暂时只支持非交互式程序题。')
		probinfo['LIMIT='] = int(prob['time limit'])
		probinfo['MEMLIMITS='] = int(prob.memory_limit().MB)
		probinfo['SAMPLES='] = len(prob.test_cases)
		score_per_case = 100 // len(prob.test_cases)
		if not prob.packed and score_per_case * len(prob.test_cases) != 100:
			log.warning(u'测试点数量不是100的约数，分数无法均分为整数。')
		probinfo['CCL=c@gcc'] = ' -o %o %i ' + prob['compile']['c']
		probinfo['CCL=cpp@g++'] = ' -o %o %i ' + prob['compile']['cpp']
		probinfo['CCL=pas@fpc'] = ' %i ' + prob['compile']['pas']
		idx = 0
		for datum in prob.data:
			if prob.packed and len(datum['cases']) > 1:
				log.warning(u'Arbiter不支持打包评测，将把该包得分均分给包中各测试点，无法整除时总分将不正确。')
			for case in datum['cases']:
			#for idx, case in enumerate(prob.test_cases, start = 1):
				idx += 1
				'''print('copyfile %s'%base.pjoin(prob.path,'data',case+'.in'))'''
				shutil.copy(
					base.pjoin(prob.path,'data',str(case)+'.in'),
					base.pjoin('arbiter', 'main','data',prob['name']+str(idx)+'.in')
				)
				'''print('copyfile %s'%base.pjoin(prob.path,'data',case+'.ans'))'''
				shutil.copy(
					base.pjoin(prob.path,'data',str(case)+'.ans'),
					base.pjoin('arbiter', 'main','data',prob['name']+str(idx)+'.ans')
				)
				if prob.packed:
					probinfo['MARK='+str(idx)+'@'] = str(int(datum['score'] / len(datum['cases'])))
				else:
					probinfo['MARK='+str(idx)+'@'] = str(int(score_per_case))
		'''for idx, userdir in enumerate(prob['users'],start = 1):
			for idx2, code in enumerate(prob['users'][userdir],start = 1):
				dirname = prob['name']+'-'+str(idx)+str(idx2)
				codename = userdir + code
				tmplist = prob['users'][userdir][code].split('/')
				codedir = base.pjoin(prob.path,*tmplist)
				os.makedirs(base.pjoin('arbiter','players',conf['name'],dirname,prob['name']))
				shutil.copy(codedir,base.pjoin('arbiter','players',conf['name'],dirname,prob['name']))
				userlist[dirname + '@'] =  codename'''
		shutil.copy(base.pjoin(base.path,'sample','arbiter_e.sample'),base.pjoin('arbiter', 'main','filter',prob['name']+'_e'))
		arbiter_info(probinfo,base.pjoin('arbiter', 'main','task'+str(daynum)+'_'+str(probnum)+'.info'))

def arbiter_down(conf = None):
	if not conf:
		conf = base.conf
		if not os.path.exists('arbiter'):
			base.remkdir('arbiter')
		base.remkdir(pjoin('arbiter', 'down'))
	if conf.folder == 'problem':
		raise Exception('Can\'t dump a single problem to arbiter, try to dump a day or a contest.')
	if conf.folder == 'contest':
		for idx, day in enumerate(base.days(), start = 1):
			os.makedirs(base.pjoin(pjoin('arbiter', 'down'), day['name']))
			arbiter_down(day)
		return
	for prob in conf.probs():
		log.info(prob.route)
		os.makedirs(base.pjoin(pjoin('arbiter', 'down'), prob.route))
		for idx, case in enumerate(prob.sample_cases, start = 1):
			for s_name, t_name in ((
				base.pjoin(prob.path,'down',str(case)+'.in'),
				base.pjoin('arbiter', 'down', prob.route, prob['name']+str(idx)+'.in')
			), (
				base.pjoin(prob.path,'down',str(case)+'.ans'),
				base.pjoin('arbiter', 'down', prob.route, prob['name']+str(idx)+'.ans')
			)):
				base.shutil_copy(s_name, t_name)
	log.info('dos2unix')
	base.run_r(base.dos2unix, base.pjoin(pjoin('arbiter', 'down', conf.route)))

def arbiter():
	base.remkdir('arbiter')
	arbiter_main()
	arbiter_down()

def tsinsen_oj():
	import random
	if type(base.conf) != base.Problem:
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
	for day in base.days():
		p = base.pjoin('tsinsen-oj', day.route)
		if not os.path.exists(p):
			os.makedirs(p)
	for prob in base.probs():
		p = base.pjoin('tsinsen-oj', prob.route)
		if not os.path.exists(p):
			os.makedirs(p)
		if os.path.exists(base.pjoin(prob.path, 'down')):
			with zipfile.ZipFile(base.pjoin('tsinsen-oj', prob.route, 'down.zip'), 'w') as z:
				base.run_r(lambda path : z.write(path), base.pjoin(prob.path, 'down'))
			prob.tsinsen_down = hash(8)
		else:
			prob.tsinsen_down = None
		files = {}
		path = base.pjoin(prob.path, 'resources')
		if os.path.exists(path):
			base.run_r(lambda p : files.__setitem__(p[len(path) + 1:], hash(8)), path)
		prob.tsinsen_files = files
	if base.do_render:
		from . import ren
		tmp = base.start_file
		base.start_file = False
		ren.Html('tsinsen-oj').run()
		base.start_file = tmp
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
		path = base.pjoin('data', 'chk', 'chk.cpp')
		if os.path.exists(path):
			return open(path, 'rb').read().decode('utf-8')
		else:
			return '\n'
	def Description():
		path = pjoin('statements', 'tsinsen-oj', prob.route if prob.route != '' else prob['name']) + '.html'
		if not os.path.exists(path):
			log.warning(u'找不到题面，你可能需要自己手工添加题面。')
			return ''
		header = u'<p>下载目录：<img src="/RequireFile.do?fid=%s" alt="另存为图片下载" />（另存为图片下载）</p>\n' % prob.tsinsen_down
		return header + read_file(path)
	def Solution():
		for user, codes in prob['users'].items():
			for name, path in codes.items():
				if prob.expect(user, name, 100):
					return read_file(path['path'])
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
	for prob in base.probs():
		result_file = base.pjoin('tsinsen-oj', prob.route) + '.txt'
		with open(result_file, 'wb') as f:
			for token in tokens:
				f.write(add_shell(token, eval(token)))
			if prob.packed:
				log.warning(u'清橙OJ不支持打包评测和指定测试点分值，直接将所有测试点视为相同。')
			for datum in prob.test_cases:
				f.write(add_shell('InData', lambda : read_file(base.pjoin('data', datum + '.in'))))
				f.write(add_shell('OutData', lambda : read_file(base.pjoin('data', datum + '.ans'))))
			if prob.tsinsen_down:
				f.write(add_shell('FileName', lambda : 'down.zip'))
				f.write(add_shell('File(%s)' % prob.tsinsen_down, lambda : to_base64(base.pjoin('tsinsen-oj', prob.route, 'down.zip'))))
			for key, val in prob.tsinsen_files.items():
				f.write(add_shell('FileName', lambda : key.replace('/', '-').replace('\\', '-')))
				f.write(add_shell('File(%s)' % val, lambda : to_base64(base.pjoin(prob.path, 'resources', key))))
		if base.start_file:
			base.xopen_file(result_file)

def tuoj_down(conf = None):
	if not conf:
		conf = base.conf
		if not os.path.exists('tuoj'):
			base.remkdir('tuoj')
		base.remkdir(pjoin('tuoj', 'down'))
	if conf.folder == 'contest':
		for day in base.days():
			os.makedirs(base.pjoin(pjoin('tuoj', 'down'), day['name']))
			tuoj_down(day)
		return
	for prob in conf.probs():
		log.info(prob.route)
		os.makedirs(base.pjoin(pjoin('tuoj', 'down'), prob.route))
		for idx, case in enumerate(prob.sample_cases, start = 1):
			shutil.copy(
				base.pjoin(prob.path, 'down', str(case) + '.in'),
				base.pjoin('tuoj', 'down', prob.route, str(case) + '.in')
			)
			shutil.copy(
				base.pjoin(prob.path, 'down',str(case) + '.ans'),
				base.pjoin('tuoj', 'down', prob.route, str(case) + '.ans')
			)
		base.run_r(base.dos2unix, base.pjoin(pjoin('tuoj', 'down', prob.route)))

def loj_prob(conf, pre = False):
	if not pre and len(conf.get('pre', [])) > 0:
		loj_prob(conf, True)
	global save_flag
	headers = {
		'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
	}
	tool_conf = base.tool_conf[base.work]['default']
	cookies = tool_conf['cookies']
	pid_key = 'pid' if not pre else 'pid-pre'
	pid = conf.get(pid_key, {}).get(base.work + '-default', 0)
	host = tool_conf['main']
	data = {
		'title' : conf.tr('title') + (u'（预测试）' if pre else ''),
		'description' : 'place holder',
		'input_format' : 'place holder',
		'output_format' : 'place holder',
		'example' : 'place holder',
		'limit_and_hint' : 'place holder',
		'tags' : conf.get('tags', {}).get(base.work + '-default', [])
	}
	def file_callback(m):
		p = (m.bytes_read / m.len) * 100
		print('上传 %.1f%%（%.1f KiB/%.1f KiB）    ' % (p, m.bytes_read / 1024, m.len / 1024), end = '\r')
		sys.stdout.flush()
	def post(url, data = None, files = None):
		if files:
			d = dict(files)
			if not data:
				data = {}
			for k, v in data.items():
				d[k] = str(v)
			d = MultipartEncoder(d)
			d = MultipartEncoderMonitor(d, file_callback)
			h = headers.copy()
			h['Content-Type'] = d.content_type
		else:
			d = data
			h = headers
		r = requests.post(
			host + url,
			headers = h,
			stream = True,
			cookies = cookies,
			data = d
		)
		if not r.ok:
			log.error(u'网站连接失败，错误代码%s，错误信息见`error.log`。' % r.status_code)
			with open('error.log', 'a') as f:
				f.write(u'运行时间：' + str(datetime.datetime.now()) + '\n')
				f.write(u'url：' + r.url + '\n')
				f.write(r.text)
		return r
	if pid == 0:
		r = post('/problem/%d/edit' % pid, data)
		pid = int(r.url.split('/')[-1])
		conf.setdefault(pid_key, {})
		conf[pid_key][base.work + '-default'] = pid
		save_flag = True
	path = pjoin('statements', base.work, conf.route if conf.route != '' else conf['name']) + '.md'
	data['description'] = open(path, 'rb').read()
	post('/problem/%d/edit' % pid, data)
	import zipfile, uuid
	conf_data = conf.data if not pre else conf.pre
	packed = conf.packed if not pre else conf.packed_pre
	cases = conf.test_cases if not pre else conf.pre_cases
	data_yml = {
		'inputFile' : '#.in',
		'outputFile' : '#.ans',
		'subtasks' : [{
			'score' : datum.score if packed else 100 / len(cases) * len(datum['cases']),
			'type' : 'min' if packed else 'sum',
			'cases' : [str(c) for c in datum['cases']]
		} for datum in conf_data]
	}
	if os.path.exists(pjoin(conf.path, 'data', 'chk', 'chk.cpp')):
		data_yml['specialJudge'] = {
			'language' : 'cpp17',
			'fileName' : 'spj_cpp.cpp'
		}
	if conf['type'] == 'output':
		data_yml['userOutput'] = '#.out'
	data_path = 'data' if not pre else 'pre'
	open(pjoin(base.work, data_path, conf.route + '.yml'), 'wb').write(base.dump_formats['yaml'](data_yml))
	def pack(z, path, fname, force_file = False):
		full_path = pjoin(path, fname)
		print(u"打包文件`%s`  " % full_path, end = '\r')
		sys.stdout.flush()
		if os.path.isdir(full_path):
			if not force_file:
				for sub in os.listdir(full_path):
					pack(z, path, pjoin(fname, sub))
				return
			else:
				log.warning(u'支持版本的`%s`不能是文件夹，用空文件代替。' % pjoin)
				id = str(uuid.uuid4()) + '.tmp'
				open(id, 'w')
		else:
			id = str(uuid.uuid4()) + '.tmp'
			base.shutil_copy(full_path, id)
		time.sleep(0.1)
		base.dos2unix(id, full_path)
		z.write(id, fname)
		os.remove(id)
	data_path = 'data' if not pre else 'pre'
	with zipfile.ZipFile(pjoin(base.work, data_path, conf.route + '.zip'), 'w') as z:
		for id in (conf.test_cases if not pre else conf.pre_cases):
			pack(z, pjoin(conf.path, data_path), id + '.in', force_file = True)
			pack(z, pjoin(conf.path, data_path), id + '.ans', force_file = True)
		if os.path.exists(pjoin(conf.path, 'data', 'chk', 'chk.cpp')):
			z.write(pjoin(conf.path, 'data', 'chk', 'chk.cpp'), 'spj_cpp.cpp')
		if os.path.exists(pjoin(base.work, data_path, conf.route + '.yml')):
			z.write(pjoin(base.work, data_path, conf.route + '.yml'), 'data.yml')
	files = [
		('testdata', ("data.zip", open(pjoin(base.work, data_path, conf.route + '.zip'), "rb"))),
	]
	with zipfile.ZipFile(pjoin(base.work, 'resources', conf.route + '.zip'), 'w') as z:
		try:
			for name in os.listdir(pjoin(conf.path, 'resources')):
				pack(z, pjoin(conf.path, 'resources'), name)
		except Exception as e:
			log.warning(u'没有找到资源文件。')
	if os.path.exists(pjoin(conf.path, 'down')) and len(list(os.listdir(pjoin(conf.path, 'down')))) > 0:
		with zipfile.ZipFile(pjoin(base.work, 'down', conf.route + '.zip'), 'w') as z:
			if conf['type'] == 'output':
				for id in conf.test_cases:
					pack(z, conf.path, pjoin('data', id + '.in'))
				for name in os.listdir(pjoin(conf.path, 'down')):
					pack(z, conf.path, pjoin('down', name))
			else:
				for name in os.listdir(pjoin(conf.path, 'down')):
					pack(z, pjoin(conf.path, 'down'), name)
		files.append(('additional_file', ("down.zip", open(pjoin(base.work, 'down', conf.route + '.zip'), "rb"))))
	data = {
		'type' : {'program' : 'traditional', 'output' : 'submit-answer', 'interactive' : 'interaction', 'hand' : 'hand'}.get(conf['type'], conf['type'])
	}
	if conf['type'] != 'output':
		data['time_limit'] = int(conf.get('time limit', 0) * 1000)
		data['memory_limit'] = int(conf.ml().MB)
	if conf.get('file io'):
		data['io_method'] = 'file-io'
		data['file_io_input_name'] = conf.get('input_table', {}).get('zh-cn', conf['name'] + '.in')
		data['file_io_output_name'] = conf.get('output_table', {}).get('zh-cn', conf['name'] + '.out')
	post('/problem/%d/manage' % pid, data, files)
	files = [
		('images', ("resources.zip", open(pjoin(base.work, 'resources', conf.route + '.zip'), "rb")))
	]
	post('/problem/%d/upload_resource' % pid, files = files)

def loj():
	global save_flag
	save_flag = False
	syz_host = base.tool_conf.get(base.work, {}).get('default')
	if not syz_host:
		log.error(u'没有配置%s的地址。' % base.work)
		if base.system == 'Windows':
			log.info(u'在tuack的安装目录中找到conf.json。')
		else:
			log.info(u'在~/.tuack中找到conf.json。')
		log.info(u'添加%s的相关字段，详见`https://git.thusaac.com/publish/tuack/wikis/导出题目`。' % base.work)
		return
	if not os.path.exists(base.work):
		base.remkdir(base.work)
	base.remkdir(pjoin(base.work, 'data'))
	base.remkdir(pjoin(base.work, 'pre'))
	base.remkdir(pjoin(base.work, 'down'))
	base.remkdir(pjoin(base.work, 'resources'))
	if base.conf.folder == 'contest':
		for day in base.days():
			os.makedirs(base.pjoin(pjoin(base.work, 'data'), day.route))
			os.makedirs(base.pjoin(pjoin(base.work, 'down'), day.route))
			os.makedirs(base.pjoin(pjoin(base.work, 'pre'), day.route))
			os.makedirs(base.pjoin(pjoin(base.work, 'resources'), day.route))
	if base.do_render:
		from . import ren
		tmp = base.start_file
		base.start_file = False
		ren.Markdown(base.work).run()
		base.start_file = tmp
	else:
		pass
	for prob in base.probs():
		try:
			loj_prob(prob)
		except Exception as e:
			traceback.print_exc()
			log.error(u'输出题目`%s`时发生错误`%s`，具体信息如上所示。' % (prob['name'], e))
	if save_flag:
		base.save_json(base.conf)
		
work_list = {
	'lemon' : lemon,
	'arbiter' : arbiter,
	'arbiter-main' : arbiter_main,
	'arbiter-down' : arbiter_down,
	'tsinsen-oj' : tsinsen_oj,
	'tuoj-down' : tuoj_down,
	'loj' : loj,
	'ipuoj' : loj
}

if __name__ == '__main__':
	try:
		if base.init():
			for base.work in base.works:
				base.run_exc(work_list[base.work])
		else:
			log.info(u'这个工具用于导出成其他类型的工程。')
			log.info(u'支持的工作：%s' % ','.join(sorted(work_list.keys())))
	except base.NoFileException as e:
		log.error(e)
		log.info(u'尝试使用`python -m tuack.gen -h`获取如何生成一个工程。')
