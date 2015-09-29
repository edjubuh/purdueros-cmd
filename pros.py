#!/usr/bin/env python

import sys
import os
import argparse
import errno
import urllib2
import imp
import zipfile

parser = argparse.ArgumentParser(description='Create and upgrade PROS projects.')
parser.add_argument('--version', '-v', action='version', version='%(prog)s 0.5')
parser.add_argument('-k', '--kernel', type=str, nargs=1, metavar='V',
                    help='Kernel version to create or upgrade project to')
parser.add_argument('directory', nargs='?', default='.',
                    help='Directory to create or upgrade. Defaults to current directory')
parser.add_argument('-s', '--site', type=str, nargs=1, metavar='SITE',
                    default='https://raw.githubusercontent.com/purduesigbots/purdueros-kernels/master/',
                    help='Use a different site to pull kernels from.')
parser.add_argument('-d', '--download', action='store_false',
		    help='Forces a redownload of the kernel\' template. Works even when --kernel is not provided.')
parser.add_argument('-f', '--force', '--fresh', action='store_true', 
                    help='Deletes all contents in the directory and fills it with a new PROS template.')
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

# create if not exists
try:
	os.makedirs(kernelDirectory)
except OSError as exception:
	if exception.errno != errno.EEXIST:
		raise
	elif args.verbose:
		print(kernelDirectory + ' already exists')

# try to fetch the latest if args.kernel is undefined
if not args.kernel:
	try:
		args.kernel = urllib2.urlopen(args.site + 'latest.kernel').read()
	except urllib2.HTTPError as exception:
		if args.verbose:
			print('Unable to fetch kernel from ' + args.site)
		pass

# if we couldn't fetch the latest online, look for the highest (alphabetically) local kernel
if not args.kernel:
	if args.verbose:
		print('Local kernels: ' + ' '.join(sorted([x[0][len(kernelDirectory):] for x in os.walk(kernelDirectory)], reverse=True)))
	args.kernel = sorted([x[0][len(kernelDirectory):] for x  in os.walk(kernelDirectory)], reverse=True)[0]

# determine if we have the downloaded kernel, if not, download it
if args.kernel in [x[len(kernelDirectory):] for x in  [x[0] for x in os.walk(kernelDirectory)]]:
	if args.verbose:
		print(args.kernel + ' is available locally.')
else:
	if args.verbose:
		print(args.kernel + ' must be downloaded.')
	downloadUrl = args.site + args.kernel + '.zip'
	try:
		from StringIO import StringIO
		zipdata = StringIO()
		zipdata.write(urllib2.urlopen(downloadUrl).read())
		zipf = zipfile.ZipFile(zipdata)
		zipf.extractall(kernelDirectory + '/' +  args.kernel + '/')
	except urllib2.HTTPError as exception: # unable to download. give up
		print('Unable to download requested kernel at ' + downloadUrl)

# give up if we don't have a kernel or a locally avialable kernel yet
if not args.kernel or not args.kernel in [x[0][len(kernelDirectory):] for x in os.walk(kernelDirectory)]:
	sys.exit('Could not obtain kernel ' + args.kernel + '. Unable to download and not locally available.')


if args.verbose:
	print('Kernel directory is: ' + kernelDirectory + '\n')
# try importing the upgrade module from the kernel directory if it's found. If not, use default one
try:
	kernelModule = 	kernelDirectory + args.kernel + '/' + args.kernel + '.py'
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
if os.path.isdir(args.directory):
	if args.force:
		if args.verbose:
			print('Overwriting directory in ' + args.directory + '\n')
		execute.create(args.directory)
	else:
		if args.verbose:
			print('Upgrading directory in ' + args.directory + '\n')
		execute.upgrade(args.directory)
else:
	if args.verbose:
		print('Creating directory in ' + args.directory + '\n')
	execute.create(args.directory)
