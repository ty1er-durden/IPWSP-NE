from __future__ import print_function
import getpass
import re
import requests
import simplejson as json
import sys

def main(ciscoApicIpAddress="100.100.0.250", ignoreSslCertificateValidationError=True):
	
	# Grab credentials
	print('Username: ', end='')
	username = raw_input()
	password = getpass.getpass()

	# Perform login & get cookie
	print("\nConnecting to '{0}'...\n".format(ciscoApicIpAddress))
	
	# No error trapping...very lazy...
	baseUrl = "https://{0}/api".format(ciscoApicIpAddress)
	url = "{0}/mo/aaaLogin.json".format(baseUrl)
	payload = {
		"aaaUser":
		{
			"attributes":
			{
				"name":username,
				"pwd":password
			}
		}
	}
	headers = {
		"Content-Type": "application/json"
	}
	response = requests.request("POST", url, data=json.dumps(payload), headers=headers, verify=(not ignoreSslCertificateValidationError))
	token = json.loads(response.content)["imdata"][0]["aaaLogin"]["attributes"]["token"]
	cookies = {
		"APIC-Cookie":token
	}

	# Query for port up/down events
	url = "{0}/node/class/eventRecord.json".format(baseUrl)
	querystring = {
		"query-target-filter":'or(eq(eventRecord.cause,"port-up"),eq(eventRecord.cause,"port-down"))',
		"order-by":'eventRecord.created|desc'
	}
	response = requests.request("GET", url, cookies=cookies, headers=headers, params=querystring, verify=(not ignoreSslCertificateValidationError))
	
	# Process content
	events = json.loads(response.content)
	i = 0
	if events.has_key('imdata'):
		if i == 0:
			print("First event as JSON:")
			print(json.dumps(events['imdata'][0], sort_keys=True, indent=2))
			print("")
			i += 1
		print("Found " + events['totalCount'] + " UP/DOWN event(s):")
		for event in events['imdata']:
			attributes = event['eventRecord']['attributes']
			try:
				port = re.match('topology\/(.+)\/phys',attributes['affected']).group(1)
				print("   [{0}] {1} >> {2}".format(attributes['created'], port, attributes['descr'].split(' ')[-1].upper()))
			except:
				pass
	else:
		print("Found 0 event(s)!!")	
	return 0

if __name__ == '__main__':
	exitcode = main()
	sys.exit(exitcode)


'''SAMPLE OUTPUT

Username: student
Password: 

Connecting to '100.100.0.250'...

First event as JSON:
{
  "eventRecord": {
    "attributes": {
      "affected": "topology/pod-1/node-101/sys/phys-[eth1/40]/phys",
      "cause": "port-up",
      "changeSet": "operSt (New: up), operStQual (New: link-up)",
      "childAction": "",
      "code": "E4205125",
      "created": "2018-01-08T17:30:13.472+00:00",
      "descr": "Port is up",
      "dn": "subj-[topology/pod-1/node-101/sys/phys-[eth1/40]/phys]/rec-4294970653",
      "id": "4294970653",
      "ind": "state-transition",
      "modTs": "never",
      "severity": "info",
      "status": "",
      "trig": "oper",
      "txId": "18374686479671627862",
      "user": "internal"
    }
  }
}

Found 18 UP/DOWN event(s):
   [2018-01-08T17:30:13.472+00:00] pod-1/node-101/sys/phys-[eth1/40] >> UP
   [2018-01-08T17:29:55.154+00:00] pod-1/node-102/sys/phys-[eth1/1] >> UP
   [2018-01-08T17:29:12.992+00:00] pod-1/node-101/sys/phys-[eth1/3] >> UP
   [2018-01-08T17:29:09.768+00:00] pod-1/node-102/sys/phys-[eth1/3] >> UP
   [2018-01-08T17:29:02.761+00:00] pod-1/node-101/sys/phys-[eth1/2] >> UP
   [2018-01-08T17:28:59.543+00:00] pod-1/node-102/sys/phys-[eth1/2] >> UP
   [2018-01-08T17:28:57.556+00:00] pod-1/node-101/sys/phys-[eth1/1] >> UP
   [2018-01-08T15:59:40.069+00:00] pod-1/node-101/sys/phys-[eth1/50] >> UP
   [2018-01-08T15:59:29.840+00:00] pod-1/node-101/sys/phys-[eth1/49] >> UP
   [2018-01-08T15:59:27.296+00:00] pod-1/node-102/sys/phys-[eth1/50] >> UP
   [2018-01-08T15:59:26.939+00:00] pod-1/node-202/sys/phys-[eth5/1] >> UP
   [2018-01-08T15:59:19.863+00:00] pod-1/node-202/sys/phys-[eth5/2] >> UP
   [2018-01-08T15:59:18.735+00:00] pod-1/node-202/sys/phys-[eth5/2] >> UP
   [2018-01-08T15:59:17.068+00:00] pod-1/node-102/sys/phys-[eth1/49] >> UP
   [2018-01-08T15:59:16.997+00:00] pod-1/node-202/sys/phys-[eth5/2] >> UP
   [2018-01-08T15:59:14.615+00:00] pod-1/node-101/sys/phys-[eth1/42] >> UP
   [2018-01-08T15:59:06.857+00:00] pod-1/node-102/sys/phys-[eth1/41] >> UP
   [2018-01-08T15:59:04.402+00:00] pod-1/node-101/sys/phys-[eth1/41] >> UP


------------------
(program exited with code: 0)
Press return to continue
'''
