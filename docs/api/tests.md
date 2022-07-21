<!-- markdownlint-disable -->

<a href="../../anta/tests.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `tests`
Module that defines various functions to test EOS devices. 


---

<a href="../../anta/tests.py#L8"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_eos_version`

```python
verify_eos_version(device, versions=None)
```

Verifies the device is running one of the allowed EOS version. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 
 - <b>`versions`</b> (list):  List of allowed EOS versions. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the device is running an allowed EOS version. `False` otherwise. 


---

<a href="../../anta/tests.py#L36"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_terminattr_version`

```python
verify_terminattr_version(device, versions=None)
```

Verifies the device is running one of the allowed TerminAttr version. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 
 - <b>`versions`</b> (list):  List of allowed TerminAttr versions. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the device is running an allowed TerminAttr version. `False` otherwise. 


---

<a href="../../anta/tests.py#L63"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_eos_extensions`

```python
verify_eos_extensions(device)
```

Verifies all EOS extensions installed on the device are enabled for boot persistence. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the device has all installed its EOS extensions enabled for boot persistence. `False` otherwise. 


---

<a href="../../anta/tests.py#L101"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_field_notice_44_resolution`

```python
verify_field_notice_44_resolution(device)
```

Verifies the device is using an Aboot version that fix the bug discussed in the field notice 44 (Aboot manages system settings prior to EOS initialization). 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the device is using an Aboot version that fix the bug discussed in the field notice 44 or if the device model is not affected. `False` otherwise. 


---

<a href="../../anta/tests.py#L192"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_uptime`

```python
verify_uptime(device, minimum=None)
```

Verifies the device uptime is higher than a value. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 
 - <b>`minimum`</b> (int):  Minimum uptime in seconds. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the device uptime is higher than the threshold. `False` otherwise. 


---

<a href="../../anta/tests.py#L220"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_reload_cause`

```python
verify_reload_cause(device)
```

Verifies the last reload of the device was requested by a user. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the device last reload was requested by a user. `False` otherwise. 


---

<a href="../../anta/tests.py#L246"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_coredump`

```python
verify_coredump(device, enable_password)
```

Verifies there is no core file. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 
 - <b>`enable_password`</b> (str):  Enable password. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the device has no core file. `False` otherwise. 


---

<a href="../../anta/tests.py#L273"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_agent_logs`

```python
verify_agent_logs(device)
```

Verifies there is no agent crash reported on the device. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the device has no agent crash reported. `False` otherwise. 


---

<a href="../../anta/tests.py#L298"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_syslog`

```python
verify_syslog(device)
```

Verifies the device had no syslog message with a severity of warning (or a more severe message) during the last 7 days. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the device had no syslog message with a severity of warning (or a more severe message) during the last 7 days. `False` otherwise. 


---

<a href="../../anta/tests.py#L325"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_cpu_utilization`

```python
verify_cpu_utilization(device)
```

Verifies the CPU utilization is less than 75%. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the device CPU utilization is less than 75%. `False` otherwise. 


---

<a href="../../anta/tests.py#L350"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_memory_utilization`

```python
verify_memory_utilization(device)
```

Verifies the memory utilization is less than 75%. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the device memory utilization is less than 75%. `False` otherwise. 


---

<a href="../../anta/tests.py#L375"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_filesystem_utilization`

```python
verify_filesystem_utilization(device, enable_password)
```

Verifies each partition on the disk is used less than 75%. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 
 - <b>`enable_password`</b> (str):  Enable password. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if each partition on the disk is used less than 75%. `False` otherwise. 


---

<a href="../../anta/tests.py#L408"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_transceivers_manufacturers`

```python
verify_transceivers_manufacturers(device, manufacturers=None)
```

Verifies the device is only using transceivers from supported manufacturers. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 
 - <b>`manufacturers`</b> (list):  List of allowed transceivers manufacturers. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the device is only using transceivers from supported manufacturers. `False` otherwise. 


---

<a href="../../anta/tests.py#L438"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_system_temperature`

```python
verify_system_temperature(device)
```

Verifies the device temperature is currently OK and the device did not report any temperature alarm in the past. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the device temperature is OK. `False` otherwise. 


---

<a href="../../anta/tests.py#L465"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_transceiver_temperature`

```python
verify_transceiver_temperature(device)
```

Verifies the transceivers temperature is currently OK and the device did not report any alarm in the past for its transceivers temperature. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the transceivers temperature of the device is currently OK and if the device did not report any alarm in the past for its transceivers temperature. `False` otherwise. 


---

<a href="../../anta/tests.py#L494"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_environment_cooling`

```python
verify_environment_cooling(device)
```

Verifies the fans status is OK. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the if the fans status is OK. `False` otherwise. 


---

<a href="../../anta/tests.py#L520"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_environment_power`

```python
verify_environment_power(device)
```

Verifies the power supplies status is OK. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the power supplies is OK. `False` otherwise. 


---

<a href="../../anta/tests.py#L547"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_zerotouch`

```python
verify_zerotouch(device)
```

Verifies ZeroTouch is disabled. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if ZeroTouch is disabled. `False` otherwise. 


---

<a href="../../anta/tests.py#L573"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_running_config_diffs`

```python
verify_running_config_diffs(device, enable_password)
```

Verifies there is no difference between the running-config and the startup-config. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 
 - <b>`enable_password`</b> (str):  Enable password. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if there is no difference between the running-config and the startup-config. `False` otherwise. 


---

<a href="../../anta/tests.py#L603"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_unified_forwarding_table_mode`

```python
verify_unified_forwarding_table_mode(device, mode=None)
```

Verifies the device is using the expected Unified Forwarding Table mode. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 
 - <b>`mode`</b> (int):  The expected Unified Forwarding Table mode. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the device is using the expected Unified Forwarding Table mode. `False` otherwise. 


---

<a href="../../anta/tests.py#L632"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_tcam_profile`

```python
verify_tcam_profile(device, profile)
```

Verifies the configured TCAM profile is the expected one. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 
 - <b>`profile`</b> (str):  The expected TCAM profile. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the device is configured with the expected TCAM profile. `False` otherwise. 


---

<a href="../../anta/tests.py#L660"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_adverse_drops`

```python
verify_adverse_drops(device)
```

Verifies there is no adverse drops on DCS-7280E and DCS-7500E switches. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the device (DCS-7280E and DCS-7500E) doesnt reports adverse drops. `False` if the device (DCS-7280E and DCS-7500E) report adverse drops. 


---

<a href="../../anta/tests.py#L686"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_ntp`

```python
verify_ntp(device)
```

Verifies NTP is synchronised. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the NTP is synchronised. `False` otherwise. 


---

<a href="../../anta/tests.py#L712"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_interface_utilization`

```python
verify_interface_utilization(device)
```

Verifies interfaces utilization is below 75%. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if interfaces utilization is below 75%. `False` otherwise. 


---

<a href="../../anta/tests.py#L743"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_interface_errors`

```python
verify_interface_errors(device)
```

Verifies interfaces error counters are equal to zero. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the interfaces error counters are equal to zero. `False` otherwise. 


---

<a href="../../anta/tests.py#L771"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_interface_discards`

```python
verify_interface_discards(device)
```

Verifies interfaces packet discard counters are equal to zero. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the interfaces packet discard counters are equal to zero. `False` otherwise. 


---

<a href="../../anta/tests.py#L799"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_interface_errdisabled`

```python
verify_interface_errdisabled(device)
```

Verifies there is no interface in error disable state. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if there is no interface in error disable state.. `False` otherwise. 


---

<a href="../../anta/tests.py#L827"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_interfaces_status`

```python
verify_interfaces_status(device, minimum=None)
```

Verifies the number of Ethernet interfaces up/up on the device is higher or equal than a value. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 
 - <b>`minimum`</b> (int):  Expected minimum number of Ethernet interfaces up/up 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the number of Ethernet interfaces up/up on the device is higher or equal than the provided value. `False` otherwise. 


---

<a href="../../anta/tests.py#L862"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_storm_control_drops`

```python
verify_storm_control_drops(device)
```

Verifies the device did not drop packets due its to storm-control configuration. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the device did not drop packet due to its storm-control configuration. `False` otherwise. 


---

<a href="../../anta/tests.py#L891"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_portchannels`

```python
verify_portchannels(device)
```

Verifies there is no inactive port in port channels. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if there is no inactive port in port channels. `False` otherwise. 


---

<a href="../../anta/tests.py#L920"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_illegal_lacp`

```python
verify_illegal_lacp(device)
```

Verifies there is no illegal LACP packets received. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if there is no illegal LACP packets received. `False` otherwise. 


---

<a href="../../anta/tests.py#L950"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_mlag_status`

```python
verify_mlag_status(device)
```

Verifies the MLAG status: state is active, negotiation status is connected, local int is up, peer link is up. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the MLAG status is OK. `False` otherwise. 


---

<a href="../../anta/tests.py#L985"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_mlag_interfaces`

```python
verify_mlag_interfaces(device)
```

Verifies there is no inactive or active-partial MLAG interfaces. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if there is no inactive or active-partial MLAG interfaces. `False` otherwise. 


---

<a href="../../anta/tests.py#L1014"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_mlag_config_sanity`

```python
verify_mlag_config_sanity(device)
```

Verifies there is no MLAG config-sanity warnings. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if there is no MLAG config-sanity warnings. `False` otherwise. 


---

<a href="../../anta/tests.py#L1042"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_loopback_count`

```python
verify_loopback_count(device, number=None)
```

Verifies the number of loopback interfaces on the device is the one we expect. And if none of the loopback is down. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 
 - <b>`number`</b> (int):  Expected number of loopback interfaces. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the device is running an allowed EOS version. `False` otherwise. 


---

<a href="../../anta/tests.py#L1071"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_vxlan`

```python
verify_vxlan(device)
```

Verifies the interface vxlan 1 status is up/up. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the interface vxlan 1 status is up/up. `False` otherwise. 


---

<a href="../../anta/tests.py#L1096"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_vxlan_config_sanity`

```python
verify_vxlan_config_sanity(device)
```

Verifies there is no VXLAN config-sanity warnings. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if there is no VXLAN config-sanity warnings. `False` otherwise. 


---

<a href="../../anta/tests.py#L1124"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_svi`

```python
verify_svi(device)
```

Verifies there is no interface vlan down. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if there is no interface vlan down. `False` otherwise. 


---

<a href="../../anta/tests.py#L1147"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_spanning_tree_blocked_ports`

```python
verify_spanning_tree_blocked_ports(device)
```

Verifies there is no spanning-tree blocked ports. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` there is no spanning-tree blocked ports. `False` otherwise. 


---

<a href="../../anta/tests.py#L1172"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_routing_protocol_model`

```python
verify_routing_protocol_model(device, model=None)
```

Verifies the configured routing protocol model is the one we expect. And if there is no mismatch between the configured and operating routing protocol model. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 
 - <b>`model`</b> (str):  Expected routing protocol model (multi-agent or ribd). 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the configured routing protocol model is the one we expect. And if there is no mismatch between the configured and operating routing protocol model. `False` otherwise. 


---

<a href="../../anta/tests.py#L1204"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_routing_table_size`

```python
verify_routing_table_size(device, minimum=None, maximum=None)
```

Verifies the size of the IP routing table (default VRF). Should be between the two provided thresholds. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 
 - <b>`minimum`</b> (int):  Expected minimum routing table (default VRF) size. 
 - <b>`maximum`</b> (int):  Expected maximum routing table (default VRF) size. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the size of the IP routing table (default VRF) is between two thresholds. `False` otherwise. 


---

<a href="../../anta/tests.py#L1234"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_bfd`

```python
verify_bfd(device)
```

Verifies there is no BFD peer in down state (all VRF, IPv4 neighbors). 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if there is no BFD peer in down state (all VRF, IPv4 neighbors, single-hop). `False` otherwise. 


---

<a href="../../anta/tests.py#L1262"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_bgp_ipv4_unicast_state`

```python
verify_bgp_ipv4_unicast_state(device)
```

Verifies all IPv4 unicast BGP sessions are established (for all VRF) and all BGP messages queues for these sessions are empty (for all VRF). 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if all IPv4 unicast BGP sessions are established (for all VRF) and all BGP messages queues for these sessions are empty (for all VRF). `False` otherwise. 


---

<a href="../../anta/tests.py#L1295"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_bgp_ipv4_unicast_count`

```python
verify_bgp_ipv4_unicast_count(device, number, vrf='default')
```

Verifies all IPv4 unicast BGP sessions are established and all BGP messages queues for these sessions are empty and the actual number of BGP IPv4 unicast neighbors is the one we expect. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 
 - <b>`number`</b> (int):  Expected number of BGP IPv4 unicast neighbors 
 - <b>`vrf`</b> (str):  VRF to verify. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if all IPv4 unicast BGP sessions are established and if all BGP messages queues for these sessions are empty and if the actual number of BGP IPv4 unicast neighbors is the one we expect. `False` otherwise. 


---

<a href="../../anta/tests.py#L1338"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_bgp_ipv6_unicast_state`

```python
verify_bgp_ipv6_unicast_state(device)
```

Verifies all IPv6 unicast BGP sessions are established (for all VRF) and all BGP messages queues for these sessions are empty (for all VRF). 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if all IPv6 unicast BGP sessions are established (for all VRF) and all BGP messages queues for these sessions are empty (for all VRF). `False` otherwise. 


---

<a href="../../anta/tests.py#L1371"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_bgp_evpn_state`

```python
verify_bgp_evpn_state(device)
```

Verifies all EVPN BGP sessions are established (default VRF). 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if all EVPN BGP sessions are established. `False` otherwise. 


---

<a href="../../anta/tests.py#L1400"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_bgp_evpn_count`

```python
verify_bgp_evpn_count(device, number)
```

Verifies all EVPN BGP sessions are established (default VRF) and the actual number of BGP EVPN neighbors is the one we expect (default VRF). 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 
 - <b>`number`</b> (int):  The expected number of BGP EVPN neighbors in the default VRF. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if all EVPN BGP sessions are established and if the actual number of BGP EVPN neighbors is the one we expect. `False` otherwise. 


---

<a href="../../anta/tests.py#L1435"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_bgp_rtc_state`

```python
verify_bgp_rtc_state(device)
```

Verifies all RTC BGP sessions are established (default VRF). 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if all RTC BGP sessions are established. `False` otherwise. 


---

<a href="../../anta/tests.py#L1464"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_bgp_rtc_count`

```python
verify_bgp_rtc_count(device, number)
```

Verifies all RTC BGP sessions are established (default VRF) and the actual number of BGP RTC neighbors is the one we expect (default VRF). 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 
 - <b>`number`</b> (int):  The expected number of BGP RTC neighbors (default VRF). 



**Returns:**
 
 - <b>`bool`</b>:  `True` if all RTC BGP sessions are established and if the actual number of BGP RTC neighbors is the one we expect. `False` otherwise. 


---

<a href="../../anta/tests.py#L1499"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_ospf_state`

```python
verify_ospf_state(device)
```

Verifies all OSPF neighbors are in FULL state. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if all OSPF neighbors are in FULL state. `False` otherwise. 


---

<a href="../../anta/tests.py#L1524"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_ospf_count`

```python
verify_ospf_count(device, number=None)
```

Verifies the number of OSPF neighbors in FULL state is the one we expect. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 
 - <b>`number`</b> (int):  The expected number of OSPF neighbors in FULL state. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the number of OSPF neighbors in FULL state is the one we expect. `False` otherwise. 


---

<a href="../../anta/tests.py#L1552"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_igmp_snooping_vlans`

```python
verify_igmp_snooping_vlans(device, vlans, configuration)
```

Verifies the IGMP snooping configuration for some VLANs. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 
 - <b>`vlans`</b> (list):  A list of VLANs 
 - <b>`configuration`</b> (str):  Expected IGMP snooping configuration (enabled or disabled) for these VLANs. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the IGMP snooping configuration for the VLANs is the one we expect. `False` otherwise. 


---

<a href="../../anta/tests.py#L1582"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

## <kbd>function</kbd> `verify_igmp_snooping_global`

```python
verify_igmp_snooping_global(device, configuration)
```

Verifies the IGMP snooping global configuration. 



**Args:**
 
 - <b>`device`</b> (jsonrpclib.jsonrpc.ServerProxy):  Instance of the class jsonrpclib.jsonrpc.ServerProxy with 
 - <b>`the uri f'https`</b>: //{username}:{password}@{ip}/command-api'. 
 - <b>`configuration`</b> (str):  Expected global IGMP snooping configuration (enabled or disabled) for these VLANs. 



**Returns:**
 
 - <b>`bool`</b>:  `True` if the IGMP snooping global configuration is the one we expect. `False` otherwise. 




---

_This file was automatically generated via [lazydocs](https://github.com/ml-tooling/lazydocs)._
