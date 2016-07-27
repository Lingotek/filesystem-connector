import sys
import os.path
import codecs
from git import Repo
from git import RemoteProgress
import pexpect

class Git_Auto:
	def __init__(self, path):
		self.path = path
		self.repo = Repo(os.getcwd())
		self.join = os.path.join
		self.repo_is_defined = False

	def initialize_repo(self, repo_directory):
		self.repo = Repo(repo_directory)
		self.repo_is_defined = True

	def add_file(self, file_name):
		assert self.repo_is_defined
		self.repo.git.add(file_name)

	def commit(self, message):
		assert self.repo_is_defined
		message.rstrip(' ')
		self.repo.index.commit("automated commit " + message)

	def encrypt(self, password):
		password = codecs.encode(password, 'base64')
		return password

	def push(self, username=None, password=None):
		assert self.repo_is_defined
		if username or password:
			g = pexpect.spawn('git push')
			g.logfile_read = sys.stdout
			if not username: username = ''
			if not password: password = ''
			while True:
				i = g.expect(['Username for .*', 'Password for .*', pexpect.EOF])
				if(i == 0):
					g.send(username+'\n')
				elif(i == 1):
					g.send(codecs.decode(password, 'base64')+'\n')
				else:
					break
		else:
			self.repo.remotes['origin'].push()