from jsonrpclib import Server
import ssl

ssl._create_default_https_context = ssl._create_unverified_context
username = "arista"
# use the password of your ATD instance
password = "aristaoy21"
ip = "192.168.0.14"

print ('Configuring leaf3')
url = "https://" + username + ":" + password + "@" + ip + "/command-api"
switch = Server(url)

with open('demo/leaf3.conf','r') as f:
    conf_list = f.read().splitlines()

conf = switch.runCmds(version=1,cmds=conf_list, autoComplete=True)
print ('Done')