# Python 2
# from ConfigParser import ConfigParser, NoOptionError
# End Python 2
# Python 3
from configparser import ConfigParser, NoOptionError
# End Python 3
from ltk.constants import CONF_DIR, CONF_FN, SYSTEM_FILE, ERROR_FN
import sys
import os.path
import codecs
from git import Repo
from git import RemoteProgress
import os
try:
	import pexpect
except: pass
import binascii
from ltk.utils import error

class Git_Auto:
	def __init__(self, path):
		self.path = path
		self.join = os.path.join
		self.repo_is_defined = False
		self.repo_directory = ""
		self.config_file_name, self.conf_parser = self.init_config_file()

	def init_config_file(self):
		config_file_name = os.path.join(self.path, CONF_DIR, CONF_FN)
		conf_parser = ConfigParser()
		conf_parser.read(config_file_name)
		return config_file_name, conf_parser

	def repo_exists(self, repo_directory=os.getcwd()):
		while repo_directory and repo_directory != "" and not (os.path.isdir(repo_directory + "/.git")):
			repo_directory = repo_directory.split(os.sep)[:-1]
			repo_directory = (os.sep).join(repo_directory)
		if not repo_directory or repo_directory == "":
			error("No Git repository found for the current directory.")
			return False
		else:
			self.repo_directory = repo_directory
			self.initialize_repo()
			return True

	def initialize_repo(self, directory=None):
		if not directory:
			self.repo = Repo(self.repo_directory)
		else:
			self.repo = Repo(directory)
		self.repo_is_defined = True

	def add_file(self, file_name):
		if not self.repo_is_defined:
			if(self.repo_exists()):
				self.repo.git.add(file_name)

	def commit(self, message):
		if not self.repo_is_defined:
			if(self.repo_exists()):
				message.rstrip(' ')
				self.repo.index.commit(message)

	def encrypt(self, password):
		# Python 2
		# password = codecs.encode(password, 'base64')
		# End Python 2
		# Python 3
		password = bytes(password, 'utf-8')
		password = codecs.encode(password, 'base64')
		password = str(password, 'utf-8')
		# End Python 3
		return password

	def push(self, username=None, password=None):
		username = self.conf_parser.get('main', 'git_username')
		password = self.conf_parser.get('main', 'git_password')
		if not self.repo_is_defined:
			if not (self.repo_exists()):
				error("No Git repository found for the current directory.")
				return
		try:
			g = pexpect.spawnu('git push')
		except:
			try:
				self.repo.git.push()
				print("Push was successful")
			except Exception as e:
				error("Git push failed!")
				print(type(e))
			return
		try:
			g.logfile_read = sys.stdout
			while True:
				i = g.expect([u'Username for .*', u'Password for .*', pexpect.EOF])
				if(i == 0):
					g.send(username+'\n')
				elif(i == 1):
					# Python 2
					# g.send(codecs.decode(password, 'base64')+'\n')
					# End Python 2
					# Python 3
					g.send(str(codecs.decode(password.encode(), 'base64'), 'utf-8')+'\n')
					# End Python 3
				else:
					break
		except Exception as e:
			print("Notice: Auto-credentials currently not operational")
		'''
		# if 'nt' not in os.name:
		# 	g = pexpect.spawnu('git push')
		# else:
		# 	try:
		# 		g = winpexpect.winspawn('git push')
		# 	except:
		# 		error("Push failed! Please confirm that the winpexpect module is up to date.")
		# 		return
		# g.logfile_read = sys.stdout
		# if not username: username = ''
		# if not password: password = ''
		# while True:
		# 	i = g.expect([u'Username for .*', u'Password for .*', pexpect.EOF])
		# 	if(i == 0):
		# 		g.send(username+'\n')
		# 	elif(i == 1):
		# 		# Python 2
		# 		# g.send(codecs.decode(password, 'base64')+'\n')
		# 		# End Python 2
  		#		# Python 3
		# 		g.send(str(codecs.decode(password.encode(), 'base64'), 'utf-8')+'\n')
		# 		# End Python 3
		# 	else:
		# 		break
		'''