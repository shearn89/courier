#!/usr/bin/env python

## notes:
## marshall data to /var/lib/courier/
## 

import time
import signal
import sys
import os
import cPickle as pickle

## Variables
watchFolder="data"
targetFolder="processed"
fileExtension=".txt"

print watchFolder
print targetFolder
print fileExtension

## Data storage
fileList = set()

try:
	copiedList = pickle.load(open("copied_files.pkl", "rb"))
except IOError:
	print "Database not found, creating new one."
	copiedList = set()

## Signal handling
def signal_handler(signal, frame):
	print("Interrupt caught!")
	pickle.dump(copiedList, open("copied_files.pkl", "wb"))
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

## Main
def push_file(filename):
	print "pushing %s to %s" % (filename, targetFolder)
	copiedList.add(filename)

while True:
	time.sleep(1)
	for root, dirs, files in os.walk(watchFolder):
		for file in files:
			if file.endswith(fileExtension):
				fn=os.path.join(root, file)
				fileList.add(fn)
				print "to copy: "
				print (fileList - copiedList)
				if fn not in copiedList:
					push_file(fn)
				print "copied: ", copiedList
