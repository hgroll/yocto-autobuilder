#!/usr/bin/env python
# Uasage: ./UploadToS3WithMD5.py ~/Code/auto_yocto_builder/


from boto.s3.connection import S3Connection
from boto.s3.key import Key
import boto, datetime, os, sys, subprocess, shutil
from sys import argv

try:
	argv[1]
except NameError:
	print "no files given"
	sys.exit(0) 
else:
	print "Uploading files..."

FILE = argv[1] 
BRANCH = argv[2]
MACHINE = argv[3]
print argv[1]
print argv[2]
print argv[3]

conn = boto.connect_s3()

bucket = conn.get_bucket('yocto')

today = datetime.date.today()
s = str(today)
k = Key(bucket)
k.key = "Releases" + "/" + s + "/" + BRANCH + "/" + MACHINE + "/" +  FILE
k.set_contents_from_filename(FILE)

