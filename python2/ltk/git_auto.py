import sys
import os.path
import codecs
from git import Repo
from git import RemoteProgress
import pexpect
import binascii

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
		self.repo.index.commit("Translations updated for " + message)

	def encrypt(self, password):
		# Python 2
		password = codecs.encode(password, 'base64')
        # Python 3
# 		password = bytes(password, 'utf-8')
# 		password = codecs.encode(password, 'base64')
# 		password = str(password, 'utf-8')
		return password

	def push(self, username=None, password=None):
		assert self.repo_is_defined
		g = pexpect.spawnu('git push')
		g.logfile_read = sys.stdout
		if not username: username = ''
		if not password: password = ''
		while True:
			i = g.expect([u'Username for .*', u'Password for .*', pexpect.EOF])
			if(i == 0):
				g.send(username+'\n')
			elif(i == 1):
				# Python 2
				g.send(codecs.decode(password, 'base64')+'\n')
       			# Python 3
# 				g.send(str(codecs.decode(password.encode(), 'base64'), 'utf-8')+'\n')
			else:
				break