import requests
from bs4 import BeautifulSoup
import sys
import getopt

			

def usage():
	print("usage: {} -up:hv [--help --verbose --username=USER --password=PW]".format(__file__))
			
# extract from html the form keys and values as dicctionary
def parseFormInputs(html,url):

	soup = BeautifulSoup(html, 'html.parser')

	#print(soup.prettify())

	params = {}

	for element in soup.find_all('input'):
		if 'name' in element.attrs.keys():
			params[element["name"]]=element["value"]
	
	element = soup.find("form")
	actionurl = None
	if element and element.get("action"):
		actionurl = element.get("action")
		if "http" not in actionurl: #not FQDN
			actionurl = "{}{}".format(url,actionurl)
		
	#action = element.attr["action"]
	#print("action:{}".format(action))
	
	return [params,actionurl]

# we get a URL using a session and extract the form parameters, which are returned	
def requestUrlandGetForm(url,session,params,text,mode="POST"):
	
	headers = {"Accept-Language": "en-US,en;"}

	
	if mode=="POST":
		r = session.post(url,data=params,headers=headers)
	elif mode=="GET":
		r = session.get(url,headers=headers)
	else:
		print("{} not supported".format(mode))
		sys.exit(1)
		
	if verbose:	
		print("{} .. {} status:{}".format(text,url,r.status_code))
	
	if not r.status_code == 200:
		print("problem with request code: {}".format(r.status_code))
		sys.exit(1)

	html_doc = r.text
	
	if "CH-LOGIN?login" in url: #if it is the BIT login we check for error texts
		#print(html_doc)
		#if any(x in html_doc for x in  ['credential is permanently locked','The login attempt has failed','Die Anmeldung ist fehlgeschlagen'] ):
			
		soup = BeautifulSoup(html_doc, 'html.parser')
		element = soup.find('span', {"class":"iconDialogError"})
		if element:
			print("Login failed: {}".format(element.string))
			sys.exit(1)
		else:
			if verbose:
				print("login ok..")

	
	params = parseFormInputs(html_doc,url)	

	return params
	
loginUrl="https://oscar.wmo.int/surface/save-state?programId="


try:
	opts, args = getopt.getopt(sys.argv[1:], "up:h", ["username=", "password=", "help"])
except getopt.GetoptError as err:
	# print help information and exit:
	print(err) # will print something like "option -a not recognized"
	usage()
	sys.exit(2)
	
username = None
password = None
verbose = False
for o, a in opts:
	if o in ("-u", "--username"):
		username=a
	elif o in ("-v", "--verbose"):
		verbose=True
	elif o in ("-p", "--password"):
		password = a
	elif o in ("-h", "--help"):
		usage()
		sys.exit(1)
	else:
		assert False, "unhandled option"

if (not username or not password):
	usage()
	sys.exit(2)


try:
	
	oscarSession = requests.Session()
	[params,nexturl]=requestUrlandGetForm(loginUrl,oscarSession,None,"initiating oscar session","GET")
		

	bitSession = requests.Session()
	[params2,nexturl]=requestUrlandGetForm(nexturl,bitSession,params,"sending SAML token to BIT")
	[params3,nexturl]=requestUrlandGetForm(nexturl,bitSession,params2,"SSO at BIT")

	#prepare for login
	params3['isiwebuserid']=username
	params3['isiwebpasswd']=password
	#so that BIT knows that we do not want to register or abort
	params3.pop('registerUser')
	params3.pop('cancelPwdLogin')

	# login
	[params4,nexturl]=requestUrlandGetForm(nexturl,bitSession,params3,"sending username and password to BIT")

	# get final SAML token
	[params5,nexturl]=requestUrlandGetForm(nexturl,bitSession,params4,"SSO2 at BIT")

	# we're back to OSCAR
	[params6,nexturl]=requestUrlandGetForm(nexturl,oscarSession,params5,"back to OSCAR")

	# OSCAR sso
	[params7,nexturl]=requestUrlandGetForm(nexturl,oscarSession,params6,"SSO at OSCAR")

	# OSCAR auth
	[params8,nexturl]=requestUrlandGetForm(nexturl,oscarSession,params7,"auth at OSCAR")



	# test if we are logged in.
	# if we are logged in the url https://oscar.wmo.int/surface/save-state?programId= returns index.html.. otherwise it returns login something

	r8=oscarSession.get(loginUrl)

	if "index.html" in r8.url:
		print("loggin ok")
	else:
		print("not logged in")

except TimeoutError:
	print("timeout..")
	sys.exit(2)