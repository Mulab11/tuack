from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install
from subprocess import check_call
import platform

def check():
	system = platform.system()
	if system == 'Linux':
		check_call("apt-get install pandoc".split())
		check_call("apt-get install git".split())
		check_call("apt-get install git-lfs".split())
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
		check()
		develop.run(self)

class PostInstallCommand(install):
	"""Post-installation for installation mode."""
	def run(self):
		check()
		install.run(self)

setup(
	name = 'tuack',
	version = 0.1,
	packages = find_packages(),
	author = 'Chen Xumin, Zhang Ruizhe',
	author_email = 'chen.xm.mu@gmail.com, 657228726@qq.com',
	url = '',
	license = 'http://www.apache.org/licenses/LICENSE-2.0.html',
	description = 'Tools for generating an OI/ICPC-styled problem or contest for multiple judges.',
	cmdclass={
		'develop': PostDevelopCommand,
		'install': PostInstallCommand,
	},
	install_requires = [
		'jinja2',
		'natsort'
	],
	package_data = {
		'tuack': ['templates/*', 'sample/*']
	}
)