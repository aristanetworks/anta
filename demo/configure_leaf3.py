from jsonrpclib import Server
username = "arista"
# use the password of your ATD instance
password = "aristaoy21"
print ('Configuring leaf3')
ip = '192.168.0.14'
url = "http://" + username + ":" + password + "@" + ip + "/command-api"
switch = Server(url)
with open('demo/leaf3.txt','r') as f:
    conf_list = f.read().splitlines()
conf = switch.runCmds(version=1,cmds=conf_list, autoComplete=True)
print ('Done')
