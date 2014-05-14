#!/usr/bin/env python

## notes:
## marshall data to /var/lib/courier/
## TODO: service script
## TODO: SSH

import time
import signal
import sys
import os
import shutil
import cPickle as pickle
import paramiko
import scp
import socket
from ConfigParser import SafeConfigParser

## Variables
config = SafeConfigParser()
config.read('etc/courier.ini')

watchFolder = config.get("Courier", "watchFolder")
targetFolder = config.get("Courier", "targetFolder")
remoteFolder = config.get("Courier", "remoteFolder")
fileExtension = config.get("Courier", "fileExtension")
targetIP = config.get("Courier", "targetIP")
move = config.getboolean("Courier", "move")
flatten = config.getboolean("Courier", "flatten")

verb="processing"
if move:
	verb="moving"
else:
	verb="copying"

print "Watching:    %s" % watchFolder
print "Target:      %s" % targetFolder
print "Extension:   %s" % fileExtension
print "Moving?      %s" % move
print "Flatten?     %s" % flatten
print "Target IP:   %s" % targetIP

## Data storage
fileList = set()

## Initialise copied list
try:
	copiedList = pickle.load(open("copied_files.pkl", "rb"))
except IOError:
	print "Database not found, creating new one."
	copiedList = set()

print "Copied files: %s " % copiedList

## Signal handling
def interrupt_handler(signal, frame):
	print "Exit requested, saving file list."
	pickle.dump(copiedList, open("copied_files.pkl", "wb"))
	print "Goodbye!"
	sys.exit(0)

def hup_handler(signal, frame):
	global copiedList
	print "SIGHUP caught, %s all files." % verb
	copiedList = copiedList - fileList
	print copiedList
	print fileList

signal.signal(signal.SIGHUP, hup_handler) # 1
signal.signal(signal.SIGINT, interrupt_handler) # 2
signal.signal(signal.SIGQUIT, interrupt_handler) # 3
signal.signal(signal.SIGTERM, interrupt_handler) # 15

###################
## Main
def push_file(filename):
	print "\npushing %s to %s" % (filename, targetFolder)
	file='/'.join(filename.split('/')[1:])
	print "file: %s" % file
	targetFile=""
	remoteFile=os.path.join(remoteFolder,os.path.split(filename)[1])
	if flatten:
		print "flatten was true!"
		targetFile=os.path.join(targetFolder,os.path.split(filename)[1])
		print targetFile
	else:
		subpath=os.path.split(file)[0]
		targetPath=os.path.join(targetFolder,subpath)
		targetFile=os.path.join(targetFolder,file)
		try:
			print "Creating directory %s " % targetPath
			os.makedirs(targetPath)
		except OSError:
			if not os.path.isdir(targetPath):
				raise
	print targetFile
	if move:
		print "moving!"
		print filename
		print targetFile
		shutil.move(filename,targetFile)
	else:
		shutil.copy(filename,targetFile)
	scp.put(filename,remoteFile)
	copiedList.add(filename)

ssh = paramiko.SSHClient()
ssh.load_system_host_keys()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
	ssh.connect(targetIP, timeout=5)
except paramiko.ssh_exception.AuthenticationException:
	print "Authentication failed, please fix manually."
	sys.exit(1)
except socket.gaierror:
	print "Address info not valid, please check config file."
	sys.exit(1)
except socket.timeout:
	print "SSH Connection timed out, please check host %s is up." % targetIP
	sys.exit(1)

scp = scp.SCPClient(ssh.get_transport())

while True:
	time.sleep(1)
	sys.stdout.write(".")
	sys.stdout.flush()
	for root, dirs, files in os.walk(watchFolder):
		for file in files:
			if file.endswith(fileExtension):
				fn=os.path.join(root, file)
				fileList.add(fn)
				if fn not in copiedList:
					push_file(fn)
