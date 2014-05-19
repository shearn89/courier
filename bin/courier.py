#!/usr/bin/env python

## notes:
## marshall data to /var/lib/courier/
## TODO: service script

import time
import signal
import sys
import os
import shutil
import cPickle as pickle
import paramiko
import scp
from scp import SCPException
import socket
from ConfigParser import SafeConfigParser

## Variables
config = SafeConfigParser()
config.read(['etc/courier.ini','/etc/courier/courier.ini'])
dbFile = config.get("Courier", "dbFile")

def load_config():
	global config
	global watchFolder
	global targetFolder 
	global remoteFolder
	global fileExtension 
	global targetIP 
	global move 
	global flatten 
	global verb

	# load the config
	config.read(['etc/courier.ini','/etc/courier/courier.ini'])
	watchFolder = os.path.expanduser(os.path.expandvars(config.get("Courier", "watchFolder")))
	targetFolder = os.path.expanduser(os.path.expandvars(config.get("Courier", "targetFolder")))
	remoteFolder = config.get("Courier", "remoteFolder")
	fileExtension = config.get("Courier", "fileExtension")
	targetIP = config.get("Courier", "targetIP")
	move = config.getboolean("Courier", "move")
	flatten = config.getboolean("Courier", "flatten")

	if move:
		verb="Moving"
	else:
		verb="Copying"

	# print the config:
	print "Watching:    %s" % watchFolder
	print "Target:      %s" % targetFolder
	print "Extension:   %s" % fileExtension
	print "Moving?      %s" % move
	print "Flatten?     %s" % flatten
	print "Target IP:   %s" % targetIP

load_config()

## Signal handling
def interrupt_handler(signal, frame):
	print "Exit requested, saving file list."
	pickle.dump(copiedList, open(dbFile, "wb"))
	print "Goodbye!"
	sys.exit(0)

def hup_handler(signal, frame):
	global copiedList
	print verb
	load_config()
	print verb
	print "SIGHUP caught. Reloading config, and %s all files still in %s" % (verb, watchFolder)
	copiedList = copiedList - fileList


## Data storage
fileList = set()

## Initialise copied list
try:
	copiedList = pickle.load(open(dbFile, "rb"))
except IOError:
	print "Database not found, creating new one."
	copiedList = set()

print "Copied files: %s " % copiedList

signal.signal(signal.SIGHUP, hup_handler) # 1
signal.signal(signal.SIGINT, interrupt_handler) # 2
signal.signal(signal.SIGQUIT, interrupt_handler) # 3
signal.signal(signal.SIGTERM, interrupt_handler) # 15

###################
## Main
def push_file(filename):
	print "%s %s to %s" % (verb, filename, targetFolder)
	file='/'.join(filename.split('/')[1:])
	targetFile=""
	remoteFile=os.path.join(remoteFolder,os.path.split(filename)[1])
	remoteFile=os.path.expandvars(os.path.expanduser(remoteFile))
	if flatten:
		targetFile=os.path.join(targetFolder,os.path.split(filename)[1])
	else:
		subpath=file[len(watchFolder):]
		targetFile=os.path.join(targetFolder,subpath)
		targetPath=os.path.dirname(targetFile)
		try:
			print "Creating directory %s " % targetPath
			os.makedirs(targetPath)
		except OSError:
			if not os.path.isdir(targetPath):
				raise
	shutil.copy(filename,targetFile)
	if actualssh:
		remoteDir=os.path.dirname(remoteFile)
		print "Sending %s to %s" % (filename, remoteFile)
		try:
			scp.put(filename,remoteFile)
		except SCPException as e:
			try:
				print "Creating remote directory ",remoteDir
				ssh.exec_command("mkdir "+remoteDir)
				scp.put(filename,remoteFile)
			except:
				print "Error sending file/creating remote directory! Exiting."
				sys.exit(1)
	if move:
		try:
			os.remove(filename)
		except OSError as e:
			if e.errno == 2:
				pass # file doesn't exist
			else:
				raise
	copiedList.add(filename)

def walk_error(error):
	if error.errno == 2:
		print error.strerror, error.filename
		sys.exit(1)
	else:
		print error.errno
		print error.strerror

## Initialise SSH conection
actualssh=True
if ( targetIP == "127.0.0.1" or targetIP == "localhost" ):
	actualssh=False

if actualssh:
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

print "Beginning monitoring..."
while True:
	time.sleep(1)
	for root, dirs, files in os.walk(watchFolder,onerror=walk_error):
		for file in files:
			if file.endswith(fileExtension):
				fn=os.path.join(root, file)
				fileList.add(fn)
				if fn not in copiedList:
					push_file(fn)
