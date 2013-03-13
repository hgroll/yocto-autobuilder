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

SRCDIR = argv[1] 
BRANCH = argv[2]
print argv[1]
print argv[2]

FILE_README = 'README'

out = open(os.path.join(SRCDIR, FILE_README), "a+")

conn = boto.connect_s3()

bucket = conn.get_bucket('yocto')

today = datetime.date.today()
s = str(today)
k = Key(bucket)
out.write("MD5SUM for build files: \n")
for path, dir, files in os.walk(SRCDIR):
	for file in files:
		k.key = "Releases" + "/" + s + "/" + BRANCH + "/" + os.path.relpath(os.path.join(path,file),SRCDIR)
		k.set_contents_from_filename(os.path.join(path,file))
		out.write(k.compute_md5(open(os.path.join(path,file)))[0] + " " + str(file) + "\n")

out.write("\nPlease refer to https://github.org for build procedure\n")
out.close()

k.key = "Releases" + "/" + s + "/" +  FILE_README
k.set_contents_from_filename(os.path.join(SRCDIR,FILE_README))
