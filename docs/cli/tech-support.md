# Get Scheduled tech-support

EOS comes with a feature that generates tech-support archive every 1 hour and save this archive under `/mnt/flash/schedule/tech-support`

```eos
leaf1#show schedule summary
Maximum concurrent jobs  1
Prepend host name to logfile: Yes
Name                 At Time       Last        Interval       Timeout        Max        Max     Logfile Location                  Status
                                   Time         (mins)        (mins)         Log        Logs
                                                                            Files       Size
----------------- ------------- ----------- -------------- ------------- ----------- ---------- --------------------------------- ------
tech-support           now         08:37          60            30           100         -      flash:schedule/tech-support/      Success


leaf1#bash ls /mnt/flash/schedule/tech-support
leaf1_tech-support_2023-03-09.1337.log.gz  leaf1_tech-support_2023-03-10.0837.log.gz  leaf1_tech-support_2023-03-11.0337.log.gz  ...
```

As it can be useful for an NRFU to save a very complete state report before a go live, ANTA has implemented a cli that retrieves these files very easily:

```bash
anta exec collect-tech-support --help

Usage: anta exec collect-tech-support [OPTIONS]

  Collect scheduled tech-support from eos devices.

Options:
  -o, --output PATH               Path for tests catalog
  -ssh, --ssh-port INTEGER        SSH port to use for connection
  -t, --tags TEXT                 List of tags using coma as separator:
                                  tag1,tag2,tag3
  --log-level, --log [debug|info|warning|critical]
                                  Logging level of the command
  --help                          Show this message and exit.
```

When you run this command, it create an archive with all tech-support available and download it locall under `--output` folder and a subfolder per device

```bash
anta exec collect-tech-support --output .personal/test --tags spin

[10:12:57] INFO     Connecting to devices...
           INFO     Created /mnt/flash/schedule/all_files.zip on device spine01
           INFO     Connected (version 2.0, client OpenSSH_7.8)
           INFO     Authentication (publickey) failed.
[10:12:58] INFO     Authentication (keyboard-interactive) successful!
           INFO     Deleted /mnt/flash/schedule/all_files.zip on spine01
           INFO     Created /mnt/flash/schedule/all_files.zip on device spine02
[10:12:59] INFO     Connected (version 2.0, client OpenSSH_7.8)
           INFO     Authentication (publickey) failed.
           INFO     Authentication (keyboard-interactive) successful!
[10:13:00] INFO     Deleted /mnt/flash/schedule/all_files.zip on spine02
           INFO     Done collecting scheduled show-tech
```

And folder structure

```bash
❯ tree .personal/test
.personal/test
├── spine01
│   └── 13 Mar 2023 09:12:57_spine01.zip
└── spine02
    └── 13 Mar 2023 09:12:57_spine02.zip

2 directories, 2 files
```
