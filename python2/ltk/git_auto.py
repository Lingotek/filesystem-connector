import sys
import os.path
import time
from git import Repo
from git import RemoteProgress

class Git_Auto:
	def __init__(self, path):
		self.path = path
		self.repo = Repo(os.getcwd())
		self.join = os.path.join

	def add_file(self, file_name):
		self.repo.git.add(file_name)

	def commit(self, message):
		current_time = (time.strftime("%Y-%m-%d %H:%M:%S"))
		message.rstrip(' ')
		self.repo.index.commit("automated commit " + message)

	def push(self):
		self.repo.remotes['origin'].push()