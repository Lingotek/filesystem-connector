import sys
import os.path
import time
from git import Repo
from git import RemoteProgress
# import pexpect

class Git_Auto:
	def __init__(self, path):
		self.path = path
		self.repo = Repo(os.getcwd())
		self.join = os.path.join
		self.repo_is_defined = False

	def add_file(self, file_name):
		self.repo.git.add(file_name)

	def commit(self, message):
		current_time = (time.strftime("%Y-%m-%d %H:%M:%S"))
		message.rstrip(' ')
		self.repo.index.commit("automated commit " + message)

	def push(self, credential_input=None):
		# g = pexpect.spawn('POST')
		# g.expect('Username for ')
		# g.send(credential_input[0])
		self.repo.remotes['origin'].push()
		# if credential_input and len(credential_input) >= 2:
		# 	g.expect('Password for %')
		# 	g.send(credential_input[1])