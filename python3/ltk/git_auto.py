import sys
import os.path
import codecs
from git import Repo
from git import RemoteProgress
import pexpect
import binascii
from ltk.utils import error

class Git_Auto:
	def __init__(self, path):
		self.path = path
		self.join = os.path.join
		self.repo_is_defined = False

	def initialize_repo(self, repo_directory):
		self.repo = Repo(repo_directory)
		self.repo_is_defined = True

	def add_file(self, file_name):
		if not self.repo_is_defined:
			error("Git repository is not defined.")
			return
		self.repo.git.add(file_name)

	def commit(self, message):
		if not self.repo_is_defined:
			error("Git repository is not defined.")
			return
		message.rstrip(' ')
		self.repo.index.commit("Translations updated for " + message)

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
		if not self.repo_is_defined:
			error("Git repository is not defined.")
			return
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
				# g.send(codecs.decode(password, 'base64')+'\n')
				# End Python 2
       			# Python 3
				g.send(str(codecs.decode(password.encode(), 'base64'), 'utf-8')+'\n')
				# End Python 3
			else:
				break