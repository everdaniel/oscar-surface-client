import requests
from bs4 import BeautifulSoup
import sys
import getopt

			

def usage():
	print("usage: {} -up:h [--help --username=USER --password=PW]".format(__file__))
			
# extract from html the form keys and values as dicctionary
def parseFormInputs(html):

	soup = BeautifulSoup(html, 'html.parser')

	#print(soup.prettify())

	params = {}

	for element in soup.find_all('input'):
		if 'name' in element.attrs.keys():
			params[element["name"]]=element["value"]
			
	return params

# we get a URL using a session and extract the form parameters, which are returned	
def requestUrlandGetForm(url,session,params,text,mode="POST"):
	
	if mode=="POST":
		r = session.post(url,data=params)
	elif mode=="GET":
		r = session.get(url)
	else:
		print("{} not supported".format(mode))
		sys.exit(1)
		
	print("{} .. {} status:{}".format(text,url,r.status_code))
	if not r.status_code == 200:
		print("problem with request code: {}".format(r.status_code))
		sys.exit(1)

	html_doc = r.text
	
	if url is bitSubmitUrl3: #if it is the BIT login we check for error texts
		#print(html_doc)
		#if any(x in html_doc for x in  ['credential is permanently locked','The login attempt has failed','Die Anmeldung ist fehlgeschlagen'] ):
			
		soup = BeautifulSoup(html_doc, 'html.parser')
		element = soup.find('span', {"class":"iconDialogError"})
		if element:
			print("Login failed: {}".format(element.string))
			sys.exit(1)
		else:
			print("login ok..")

	
	params = parseFormInputs(html_doc)	

	return params
	
loginUrl="https://oscar.wmo.int/surface/save-state?programId="
bitSubmitUrl="https://feds.eiam.admin.ch/adfs/ls/"
bitSubmitUrl2="https://idp-base.gate.eiam.admin.ch/auth/saml2/sso/CH-LOGIN"
bitSubmitUrl3="https://idp-base.gate.eiam.admin.ch/auth/saml2/sso/CH-LOGIN?login&language=en"
loginUrl2="https://oscar.wmo.int/auth/saml2/acs"
loginUrl3="https://oscar.wmo.int/auth/saml2/sso"
loginUrl4="https://oscar.wmo.int/surface/auth"


try:
	opts, args = getopt.getopt(sys.argv[1:], "up:h", ["username=", "password=", "help"])
except getopt.GetoptError as err:
	# print help information and exit:
	print(err) # will print something like "option -a not recognized"
	usage()
	sys.exit(2)
	
username = None
password = None
for o, a in opts:
	if o in ("-u", "--username"):
		username=a
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


oscarSession = requests.Session()
params=requestUrlandGetForm(loginUrl,oscarSession,None,"initiating oscar session","GET")
	

bitSession = requests.Session()
params2=requestUrlandGetForm(bitSubmitUrl,bitSession,params,"sending SAML token to BIT")
params3=requestUrlandGetForm(bitSubmitUrl2,bitSession,params2,"SSO at BIT")

#prepare for login
params3['isiwebuserid']=username
params3['isiwebpasswd']=password
#so that BIT knows that we do not want to register or abort
params3.pop('registerUser')
params3.pop('cancelPwdLogin')

# login
params4=requestUrlandGetForm(bitSubmitUrl3,bitSession,params3,"sending username and password to BIT")

# get final SAML token
params5=requestUrlandGetForm(bitSubmitUrl,bitSession,params4,"SSO2 at BIT")

# we're back to OSCAR
params6=requestUrlandGetForm(loginUrl2,oscarSession,params5,"back to OSCAR")

# OSCAR sso
params7=requestUrlandGetForm(loginUrl3,oscarSession,params6,"SSO at OSCAR")

# OSCAR auth
params8=requestUrlandGetForm(loginUrl4,oscarSession,params7,"auth at OSCAR")



# test if we are logged in.
# if we are logged in the url https://oscar.wmo.int/surface/save-state?programId= returns index.html.. otherwise it returns login something

r8=oscarSession.get(loginUrl)

if "index.html" in r8.url:
	print("loggin ok")
else:
	print("not logged in")
