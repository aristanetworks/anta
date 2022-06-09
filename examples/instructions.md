## Network description

- 1 POD with 2 spines and 4 leaves running EOS.
- eBGP is configured between spines and leaves.
- Leaves <-> spines interfaces are configured with an IPv4 address.
- No overlay configuration.
- 1 loopback per device.
- Default VRF only.
- MLAG on leaves


## Clone the repository

```
git clone https://github.com/arista-netdevops-community/network_tests_automation.git
cd network_tests_automation
ls examples
```

## Install the requirements

```
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip list
```

## Install some additionnal tools

```
sudo apt-get install tree
sudo apt install unzip
```

## Check requirements on the switches

```
ssh arista@192.168.0.10
spine1#show management api http-commands
```

## Test devices reachability using EAPI

```
from jsonrpclib import Server
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
username = "arista"
password = "aristaoy21"
ip = "192.168.1.14"
url = "https://" + username + ":" + password + "@" + ip + "/command-api"
switch = Server(url)
result=switch.runCmds(1,['show version'], 'text')
print(result[0]['output'])
```

## Test devices reachability

```
python ./check-devices-reachability.py --help
more examples/pod.txt
python ./check-devices-reachability.py -i examples/pod.txt -u arista
```

## Collect commands output from EOS devices

```
python ./collect-eos-commands.py --help
more examples/eos-commands.yaml
python ./collect-eos-commands.py -i examples/pod.txt -c examples/eos-commands.yaml -o examples/outdir -u arista
tree examples/outdir/
more examples/outdir/192.168.0.10/text/show\ version
more examples/outdir/192.168.0.10/json/show\ version
```

## Clear counters on EOS devices

```
spine1#sh interfaces counters
```
```
python ./clear_counters.py --help
python ./clear_counters.py -i examples/pod.txt -u arista
```
Note: The script includes also the EOS command `clear hardware counter drop` which is not implemented on vEOS/cEOS.
```
spine1#sh interfaces counters
```

## Clear on devices the list of MAC addresses which are blacklisted in EVPN

```
spine1#show bgp evpn host-flap
spine1#show logging | grep EVPN-3-BLACKLISTED_DUPLICATE_MAC
```
```
python ./evpn-blacklist-recovery.py --help
```
```
spine1#show bgp evpn host-flap
```

## Collect the scheduled show tech-support files from EOS devices

```
spine1#sh running-config all | grep tech
spine1# bash ls /mnt/flash/schedule/tech-support/
```
```
python ./collect_sheduled_show_tech.py --help
python ./collect_sheduled_show_tech.py -i examples/pod.txt -u arista -o examples/outdir
ls examples/outdir
unzip examples/outdir/xxxx.zip -d examples/outdir/
ls examples/outdir/mnt/flash/schedule/tech-support/
```
```
spine1# bash ls /mnt/flash/schedule/tech-support/
```

## Run tests on devices

```
python ./check-devices.py --help
```
```
more pod.txt
more spines.txt
more leaves.txt
```
```
more pod_tests.yaml
more spines_tests.yaml
more leaves_tests.yaml
```
```
python ./check-devices.py -i examples/pod.txt -t examples/pod_tests.yaml -o examples/pod_results.txt -u arista
cat examples/pod_results.txt
```
```
python ./check-devices.py -i examples/spines.txt -t examples/spines_tests.yaml -o examples/spines_results.txt -u arista
cat examples/spines_results.txt
```
```
python ./check-devices.py -i examples/leaves.txt -t examples/leaves_tests.yaml -o examples/leaves_results.txt -u arista
cat examples/leaves_results.txt
```