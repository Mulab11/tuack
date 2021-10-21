from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install
from subprocess import check_call
import platform

def check():
	system = platform.system()
	if system == 'Linux':
		check_call("sudo apt-get install pandoc git git-lfs".split())
		check_call("git lfs install".split())
	elif system == 'Darwin':
		check_call("brew update".split())
		check_call("brew install pandoc".split())
		check_call("brew install git".split())
		check_call("brew install git-lfs".split())
		check_call("git lfs install".split())

class PostDevelopCommand(develop):
	"""Post-installation for development mode."""
	def run(self):
		#check()
		develop.run(self)

class PostInstallCommand(install):
	"""Post-installation for installation mode."""
	def run(self):
		#check()
		install.run(self)

requires = [
	'jinja2 >= 2.10',
	'natsort >= 6.0.0',
	'pyyaml >= 5.1',
	'rarfile >= 3.0'
]

setup(
	name = 'tuack',
	version = '0.1.4.12',
	packages = find_packages(),
	author = 'Chenxu Min, Zhang Ruizhe, Liu Xiaoyi, Chen Junkun, Chen Shengqi, Luo Lingxiao',
	author_email = 'chen.xm.mu@gmail.com, 657228726@qq.com, circuitcoder0@gmail.com, 1261954105@qq.com, i@harrychen.xyz',
	url = '',
	license = 'https://git.thusaac.com/publish/tuack/blob/master/LICENSE',
	description = 'Tools for generating an Tsinghua/OI/ICPC-styled problem or contest for multiple judges.',
	cmdclass={
		'develop': PostDevelopCommand,
		'install': PostInstallCommand,
	},
	#requires = requires,
	install_requires = requires,
	setup_requires = requires,
	package_data = {
		'tuack': [
			'templates/*.*', 'templates/*/*/*',
			'sample/*.*', 'sample/*/*',
			'sample-problem/*.*', 'sample-problem/*/*',
			'sample-empty/*.*', 'sample-empty/*/*',
			'lex/*.*', 'lex/*'
		]
	}
)

