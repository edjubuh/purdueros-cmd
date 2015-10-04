#!/usr/bin/env python

import sys
import os
import argparse
import errno
import urllib2
import imp
import zipfile
import tempfile

parser = argparse.ArgumentParser(description='Create and upgrade PROS projects.')
parser.add_argument('--version', '-v', action='version', version='%(prog)s 0.5')
parser.add_argument('-k', '--kernel', type=str, nargs=1, metavar='V',
                    help='Kernel version to create or upgrade project to')
parser.add_argument('directory', nargs='?', default='.',
                    help='Directory to create or upgrade. Defaults to current directory')
parser.add_argument('-s', '--site', type=str, metavar='SITE',
                    default='https://raw.githubusercontent.com/edjubuh/purdueros-kernels/master/',
                    help='Use a different site to pull kernels from.')
parser.add_argument('-d', '--download', action='store_true',
		    help='Forces a redownload of the kernel\' template. Works even when --kernel is not provided.')
parser.add_argument('-f', '--force', '--fresh', action='store_true', 
                    help='Deletes all contents in the directory and fills it with a new PROS template.')
parser.add_argument('-n', '--name', '--project-name', type=str, nargs=1, metavar='NAME',
                    help='Name of the project. Defaults to the name of the current directory')
parser.add_argument('--verbose', action='store_true',
		    help='Prints verbosely.')

args = parser.parse_args()
if args.kernel:
	args.kernel = args.kernel[0]

# determine the location of the local kernel repository
if os.name == 'posix':
	kernelDirectory = '/home/'+ os.getlogin() + '/pros/kernels/'
elif os.name == 'nt':
	kernelDirectory = 'C:\ProgramData\PROS\kernels'

if args.verbose:
	print('Kernel directory is ' + kernelDirectory)

# create if not exists
try:
	os.makedirs(kernelDirectory)
except OSError as exception:
	if exception.errno != errno.EEXIST:
		raise
	elif args.verbose:
		print(kernelDirectory + ' already exists')

# try to fetch the latest kernel version online if args.kernel is undefined
if not args.kernel:
	if args.verbose:
		print('Determining latest kernel from internet.')
	try:
		args.kernel = urllib2.urlopen(args.site + 'latest.kernel').read()
		if args.verbose:
			print('Latest kernel version is ' + args.kernel)
	except urllib2.HTTPError as exception:
		if args.verbose:
			print('Unable to fetch kernel from ' + args.site + 'latest.kernel')
		pass

# if we couldn't fetch the latest online, look for the highest (alphabetically) local kernel
if not args.kernel:
	if args.verbose:
		print('All local kernels: ' + ' '.join(sorted([x[1] for x in os.walk(kernelDirectory)][0])))
	args.kernel = sorted([x[1] for x in os.walk(kernelDirectory)][0])[0]

args.kernel = args.kernel.strip()

# give up if we still don't have a target kernel
if not args.kernel:
    sys.exit('Error: Could not determine a target kernel.')

# determine if we have the downloaded kernel, if not, download it
if not args.kernel in [x[1] for x in os.walk(kernelDirectory)][0] or args.download:
	if args.verbose:
		print(args.kernel + ' must be downloaded.')
	downloadUrl = args.site + args.kernel + '.zip'
	try:
		from StringIO import StringIO
		zipdata = StringIO()
		tempf = tempfile.NamedTemporaryFile(mode='w+b', suffix='.zip', delete=False)
		tempf.write(urllib2.urlopen(downloadUrl).read())
		tempf.close()
		zipf = zipfile.ZipFile(tempf.name)
		zipf.extractall(kernelDirectory + os.path.sep +  args.kernel + os.path.sep)
	except urllib2.HTTPError as exception: # unable to download. give up
		print('Unable to download requested kernel at ' + downloadUrl)
elif args.kernel in [x[1] for x in os.walk(kernelDirectory)][0]:
	if args.verbose:
		print(args.kernel + ' is available locally.')

# give up if we don't have a kernel or a locally avialable kernel yet
if not args.kernel or not args.kernel in [x[0][len(kernelDirectory) + 1:] for x in os.walk(kernelDirectory)]:
	sys.exit('Error: Could not obtain kernel ' + args.kernel + '. Unable to download and not locally available.')

if args.verbose:
	print('Kernel directory is: ' + kernelDirectory + os.path.sep + args.kernel + '\n')

# try importing the upgrade module from the kernel directory if it's found. If not, use default one
try:
	kernelModule = 	kernelDirectory + args.kernel + os.path.sep + args.kernel + '.py'
	if args.verbose:
		print('Attempting to load ' + kernelModule)
	execute = imp.load_source(args.kernel, kernelModule)
except IOError as exception:
	if args.verbose:
		print('Not found. Using default.')
	import defaultUpgrader
	execute = defaultUpgrader

# determine if directory exists. If it does, use the force argument to determine if to create or upgrade
# if directory doesn't exist, just create it
if args.verbose:
	print('Changing pathname. ' + args.directory + ' -> ' + os.path.abspath(args.directory))

args.directory = os.path.abspath(args.directory)

if not args.name:
	args.name = args.directory.split(os.path.sep)[-1]

if args.verbose:
	print('Project name is: ' + args.name)

if os.path.isdir(args.directory):
	if args.force:
		if args.verbose:
			print('Overwriting project in ' + args.directory + '\n')
		execute.create(args.directory, kernelDirectory + os.path.sep + args.kernel, args.name)
	else:
		if args.verbose:
			print('Upgrading project in ' + args.directory + '\n')
		execute.upgrade(args.directory, kernelDirectory + os.path.sep +  args.kernel, args.name)
else:
	if args.verbose:
		print('Creating project in ' + args.directory + '\n')
	execute.create(args.directory, kernelDirectory + os.path.sep +  args.kernel, args.name)
