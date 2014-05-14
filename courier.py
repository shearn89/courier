#!/usr/bin/env python

import time
import signal
import sys
import os

## Signal handling
def signal_handler(signal, frame):
	print("Interrupt caught!")
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

## Variables
watchFolder="data"
targetFolder="processed"
fileExtension=".txt"

print watchFolder
print targetFolder
print fileExtension

## Data storage
fileList = set()
copiedList = set()

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
