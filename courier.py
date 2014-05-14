#!/usr/bin/env python

## notes:
## marshall data to /var/lib/courier/
## add a sighup trap to re-push?

import time
import signal
import sys
import os
import shutil
import cPickle as pickle

## Variables
watchFolder="data"
targetFolder="processed"
fileExtension=".txt"
move=False
flatten=True

print "Watching:    %s" % watchFolder
print "Target:      %s" % targetFolder
print "Extension:   %s" % fileExtension
print "Moving?      %s" % move
print "Flatten?     %s" % flatten

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
	print("Interrupt caught!")
	pickle.dump(copiedList, open("copied_files.pkl", "wb"))
	sys.exit(0)

def hup_handler(signal, frame):
	global copiedList
	print("SIGHUP caught, copying all files.")
	copiedList = copiedList - fileList

signal.signal(signal.SIGINT, interrupt_handler)
signal.signal(signal.SIGHUP, hup_handler)

###################
## Main
def push_file(filename):
	print "\npushing %s to %s" % (filename, targetFolder)
	file='/'.join(filename.split('/')[1:])
	print "file: %s" % file
	subpath=os.path.split(file)[0]
	targetPath=os.path.join(targetFolder,subpath)
	print os.path.split(targetPath)[0]
	targetFile=os.path.join(targetFolder,file)
	print "target: %s" % targetFile
	try:
		print "Creating directory %s " % targetPath
		os.makedirs(targetPath)
	except OSError:
		if not os.path.isdir(targetPath):
			raise
	if move:
		shutil.move(filename,targetFile)
	else:
		shutil.copy(filename,targetFile)
	copiedList.add(filename)

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
