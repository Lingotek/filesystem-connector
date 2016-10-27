import sys
import os.path
import codecs
from git import Repo
from git import RemoteProgress
import os
try:
	import pexpect
	import winpexpect
except:
	if 'nt' in os.name:
		print("Git credentials auto-input disabled: module not supported.")
import binascii
from ltk.utils import error

class Git_Auto:
	def __init__(self, path):
		self.path = path
		self.join = os.path.join
		self.repo_is_defined = False
		self.repo_directory = ""

	def repo_exists(self, repo_directory=os.getcwd()):
		while repo_directory and repo_directory != "" and not (os.path.isdir(repo_directory + "/.git")):
			repo_directory = repo_directory.split(os.sep)[:-1]
			repo_directory = (os.sep).join(repo_directory)
		if not repo_directory or repo_directory == "":
			error("No Git repository found for the current directory.")
			return False
		else:
			self.repo_directory = repo_directory
			return True

	def initialize_repo(self, directory=None):
		if not directory:
			self.repo = Repo(self.repo_directory)
		else:
			self.repo = Repo(directory)
		self.repo_is_defined = True

	def add_file(self, file_name):
		if not self.repo_is_defined:
			error("No Git repository found for the current directory.")
			return
		self.repo.git.add(file_name)

	def commit(self, message):
		if not self.repo_is_defined:
			error("No Git repository found for the current directory.")
			return
		message.rstrip(' ')
		self.repo.index.commit("Translations updated for " + message)

	def encrypt(self, password):
		# Python 2
		password = codecs.encode(password, 'base64')
        # End Python 2
        # Python 3
# 		password = bytes(password, 'utf-8')
# 		password = codecs.encode(password, 'base64')
# 		password = str(password, 'utf-8')
        # End Python 3
		return password

	def push(self, username=None, password=None):
		if not self.repo_is_defined:
			error("No Git repository found for the current directory.")
			return
		print("Push was successful!")
		try:
			pexpect.spawnu('git push')
		except:
			try:
				g = winpexpect.winspawn('git push')
			except:
				error("Initial push failed! Retrying...")
				try:
					self.repo.git.push()
					print("Push was successful")
				except:
					error("Failed again!")
				return
		try:
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
					# End Python 2
	       			# Python 3
# 					g.send(str(codecs.decode(password.encode(), 'base64'), 'utf-8')+'\n')
					# End Python 3
				else:
					break
		except:
			print("Notice: Auto-credentials currently not operational")
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
				g.send(codecs.decode(password, 'base64')+'\n')
		# 		# End Python 2
  #      			# Python 3
# 		# 		g.send(str(codecs.decode(password.encode(), 'base64'), 'utf-8')+'\n')
		# 		# End Python 3
		# 	else:
		# 		break