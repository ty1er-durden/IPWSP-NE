#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Does some stuff with a Cisco Router

This script was created during the IPWSP-NE training course as a learning exercise.  
It might server as a useful reference for all the things that I learned to do in Python.
on the course.  Docstrings was not one of those things!

Example:
   Run the script like this:

      $ python configure-cisco-router.py --username cisco --password cisco --exportConfig --verbose 10.10.10.1 10.10.10.99

      Parsed arguments:
         username: cisco
         exportConfig: True
         password: cisco
         ipaddress: ['10.10.10.1', '10.10.10.99', '10.10.10.2']
         verbose: True
      Connecting to '10.10.10.1'...
      Setting hostname to 'Router1'...
      Retrieving running config information...
      Hostname is 'Router1'.  Update successful.
      Retrieving version information...
      Retrieving inventory...
      Router information:
         RELEASE: fc1
         IP: 10.10.10.1
         SERIAL: 4294967295
         HOSTNAME: Router1
         VERSION: 12.2(33)SRE5
      Exported running config for 10.10.10.1 to /home/student/Desktop/10.10.10.1_show_run_2018-01-31_22.40.33.txt
      Connecting to '10.10.10.99'...
      Failed to connect to '10.10.10.99'. Error 113: No route to host

"""

import paramiko
import re
import sys
import time
import argparse
import os

class Router():
	"""
	Represents a generic router object
	"""
	def __init__(self, ip):
		self.ip = ip
		self.hostname = 'unknown'
		self.serial = 'unknown'
		self.version = 'unknown'
		self.release = 'unknown'
		
	def printInfo(self):
		"""
		Prints information about a router
		"""
		print('Router information:')
		properties = vars(self)
		for key in properties.keys():
			print('   ' + str(key).upper() + ': ' + str(properties[key]))
			
class CiscoRouterSshConnection():
	"""
	Interacts with Cisco Routers via SSH
	"""
	def __init__(self, ipaddr):
		# Create client
		self.ip = ipaddr
		self.ssh_client = paramiko.SSHClient()
		self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		
	def connect(self, username, password):
		# Create connection
		self.ssh_client.connect(self.ip, username=username, password=password, look_for_keys=False, allow_agent=False)
		self.ssh_shell = self.ssh_client.invoke_shell()
		self.ssh_shell.send('terminal length 0\n')
		self.ssh_shell.send('enable\n')
		self.ssh_shell.send('{0}\n'.format(password))
		time.sleep(1)
		self.ssh_shell.recv(65535)
	
	def sendCommand(self, command):
		try:
			self.ssh_shell.send(command + "\n")
			time.sleep(1)
			output = self.ssh_shell.recv(65535)
		except IOError as e:
			print "Failed execute command '{0}'. Error {1}: {2}".format(command,e.errno, e.strerror)
		else:
			return output
		
	def getRunningConfig(self):
		return self.sendCommand('show run')
		
	def getVersion(self):
		return self.sendCommand('show version')
		
	def getInventory(self):
		return self.sendCommand('show inventory')		
	
	def setHostname(self, hostname):
		self.enterConf()
		self.sendCommand('hostname {0}'.format(hostname)) 
		self.exitConf()

	def enterConf(self):	
		self.ssh_shell.send('conf t\n')
		time.sleep(1)
		self.ssh_shell.recv(65535)
		
	def exitConf(self):
		self.ssh_shell.send("end\n")
		time.sleep(1)
		self.ssh_shell.recv(65535)
			
	def close(self):
		self.ssh_shell.send("disable\n")
		self.ssh_shell.recv(65535)
		self.ssh_client.close()

def writeToFile(text, filePath):
	"""
	Writes text to a file
	"""	
	try:
		myFile = open(filePath.strip(), "w")
		try:
			myFile.write(str(text))
		except IOError as e:
			print "Failed to write to file. Error {0}: {1}".format(e.errno, e.strerror)
		except:
			print "Unexpected error: {0}".format(sys.exc_info()[0])
		finally:
			myFile.close()
	except IOError as e:
		print "Failed to open file for writing. Error {0}: {1}".format(e.errno, e.strerror)
	except:
		print "Unexpected error: {0}".format(sys.exc_info()[0])

def main():
	
	# Deal with command-line arguments
	parser = argparse.ArgumentParser(description='Does some stuff with a Cisco Router')
	parser.add_argument('ipaddress', metavar='ipaddress', type=str, nargs='+', help='IPv4 address(es) of Cisco Router to inspect/change')
	parser.add_argument('--username', type=str, help='Username to use to authenticate')
	parser.add_argument('--password', type=str, help='Password to use to authenticate ')
	parser.add_argument('--exportConfig', help='Password to use to authenticate ', action='store_true')
	parser.add_argument('--verbose', help='Display verbose information to the screen', action='store_true')
	
	args = parser.parse_args()
	
	VERBOSE = args.verbose
	EXPORTCONFIG = args.exportConfig
	EXPORTDIR = os.environ['HOME'] + '/Desktop/'
	IPADDRESSES = args.ipaddress
	USERNAME = args.username
	PASSWORD = args.password
		
	if args.verbose:
		VERBOSE = True
		properties = vars(args)
		print('\nParsed arguments:')
		for key in properties.keys():
			print('   ' + str(key) + ': ' + str(properties[key]))
	if args.exportConfig:
		EXPORTCONFIG = True
		
	# Create objects to represent routers
	routers = []
	for ipaddress in IPADDRESSES:
		routers.append(Router(ipaddress))
	
	# Do the fun SSH stuff to pull back/update as desired
	fileList = {}
	for router in routers:
		newRouterHostName = 'Router' + router.ip.split('.')[-1]
		# Connect
		if VERBOSE:
			print("Connecting to '" + router.ip + "'...")
		try:
			routerSshConnection = CiscoRouterSshConnection(router.ip)
			routerSshConnection.connect(USERNAME, PASSWORD)
		except IOError as e:
			print "Failed to connect to '{0}'. Error {1}: {2}".format(router.ip, e.errno, e.strerror)
			continue
		except:
			print "Unexpected error: {0}".format(sys.exc_info()[0])
			continue

		# Set hostname
		if VERBOSE:
			print("Setting hostname to '" + newRouterHostName + "'...")
		routerSshConnection.setHostname(newRouterHostName)
		if VERBOSE:
			print("Retrieving running config information...")		
		runningConf = routerSshConnection.getRunningConfig()
		# Verify hostname was updated
		m = re.search('hostname\s+(?P<hostname>\S+)', runningConf)
		if hasattr(m, 'groups'):
			if len(m.groups()) == 1:
				router.hostname = m.group('hostname')
				if m.group('hostname') == newRouterHostName:
					if VERBOSE:
						print("Hostname is '" + m.group('hostname') + "'.  Update successful.")
				else:
					if VERBOSE:
						print("Hostname is '" + m.group('hostname') + "'.  Update failed.")
			else:
				if VERBOSE:
					print("Found multiple hostnames (recommend verifying config manually).  Unable to verify change was successful.")
		else:
			if VERBOSE:
				print("Unable to get hostname from running config.  Unable to verify change was successful.")
		# Get version and release
		if VERBOSE:
			print("Retrieving version information...")
		showVersion = routerSshConnection.getVersion()
		try:
			regex = 'version (?P<version>[^,]+), release software \((?P<release>\S+)\)'
			m = re.search(regex, showVersion, re.I)
			router.version = m.group('version')
			router.release = m.group('release')
		except:
			pass
		# Get serial number
		if VERBOSE:
			print("Retrieving inventory...")
		showInventory = routerSshConnection.getInventory()
		try:
			regex = 'PID:.*VID:.*SN:\s+([0-9]+)'
			m = re.search(regex, showInventory)
			router.serial = m.group(1)
		except:
			pass		
		routerSshConnection.close()		
		# Print router info
		router.printInfo()
		
		# Export configs
		if EXPORTCONFIG:
			filePath = EXPORTDIR + router.ip + '_show_run_' + time.strftime("%Y-%m-%d_%H.%M.%S") + '.txt'
			try:
				writeToFile(runningConf, filePath)
				fileList[router.ip] = filePath
				if VERBOSE:
					print("Exported running config for {0} to {1}".format(router.ip, filePath))
			except:
				print("Failed to export running config for {0}".format(router.ip))
				
	return 0

if __name__ == '__main__':
	main()
