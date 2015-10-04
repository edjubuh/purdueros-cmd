#!/usr/bin/env python

# The default upgrader module assumes the following files need to be upgraded:
#	- firmware/libccos.a
#	- firmware/uniflash.jar
#	- include/API.h
#	- src/Makefile
#	- Makefile

# The default upgrader module assumes the following files exist beyond the ones listed above
#	- .project

import os, errno
import shutil
import tempfile

upgradeFiles = ['firmware' + os.path.sep + 'libccos.a', 
				'firmware' + os.path.sep + 'uniflash.jar', 
				'include' + os.path.sep + 'API.h',
				'src' + os.path.sep + 'Makefile',
				'Makefile' ]

def upgrade(path, kernel, projectName):
	for foo in upgradeFiles: 
		print('Upgrading ' + foo)
		shutil.copyfile(kernel + os.path.sep + foo, path + os.path.sep + foo)
		
	print('\nUpgraded project to ' + kernel.split(os.path.sep)[-1])

def create(path, kernel, projectName):
	if(os.path.exists(path)):
		print('Directory already exists, removing.')
		shutil.rmtree(path)
	
	copyText = 'Copying from ' + kernel.split(os.path.sep)[-1] + '...'
	print(copyText),
	shutil.copytree(kernel, path)
	copiedText = 'Copied from ' + kernel.split(os.path.sep)[-1] 
	print('\r' + copiedText + ' ' * (len(copyText) - len(copiedText)))
	
	print('Fixing template files')
	replaceTextInFile(path + os.path.sep + '.project', 'Default_VeX_Cortex', projectName)


def replaceTextInFile(path, original, new):
	tempf = tempfile.NamedTemporaryFile(delete=False)
	foo_file = open(path, 'r')
	for line in foo_file:
		tempf.write(line.replace(original, new))
	foo_file.close()
	tempf_path = tempf.name
	tempf.close()
	tempf = open(tempf_path, 'r')
	os.unlink(path)
	foo_file = open(path, 'w')
	for line in tempf:
		foo_file.write(line)