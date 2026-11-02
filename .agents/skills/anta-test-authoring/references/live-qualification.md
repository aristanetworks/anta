# Live EOS/vEOS qualification

Use this reference only when the user requests live evidence. Live access is
read-only by default and is never a substitute for unit fixtures.

## Inputs and target selection

- Read the documented vEOS test-bed note when it is available.
- Select at least one recent F release, one M release, and the release called
  out by the requested behavior. Example targets from the documented bench are
  `veos-4-36-1f` and `veos-4-34-5m`.
- Require `LAB_USERNAME` in the invoking process environment. Do not evaluate
  or source an arbitrary `.envrc` from the skill.
- Use `--prompt` for an interactive eAPI password when the device requires
  one. Never place the password in YAML, shell history, generated reports, or
  committed files.

## Temporary inventory

Create the inventory outside the repository and keep it credential-free:

```yaml
anta_inventory:
  hosts:
    - host: veos-4-36-1f.fun.aristanetworks.com
      name: veos-4-36-1f
      tags: [veos, f]
    - host: veos-4-34-5m.fun.aristanetworks.com
      name: veos-4-34-5m
      tags: [veos, m]
```

The exact names and FQDN suffix must come from the current lab note or the
user's explicit target list. Do not commit DHCP addresses.

## Collect the command schema

For each selected device, use the ANTA CLI with a temporary inventory:

```bash
uv run anta debug run-cmd \
  --username "$LAB_USERNAME" \
  --prompt \
  --inventory /tmp/anta-live/inventory.yml \
  --device <device-name> \
  --command "<show command>" \
  --ofmt json \
  --revision <revision>
```

Record only sanitized evidence containing device release, command, revision,
and the relevant schema observations. Compare list/map nesting, missing keys,
state names, and address/VRF representations before choosing the class logic.

## Run a catalog live

Keep the live catalog in the same temporary directory and use a narrow device
or tag selection:

```bash
uv run anta nrfu \
  --username "$LAB_USERNAME" \
  --prompt \
  --inventory /tmp/anta-live/inventory.yml \
  --catalog /tmp/anta-live/catalog.yml \
  --device <device-name> \
  table
```

Use the actual exit status as evidence. If a failure is expected for a known
non-established live state, label it as an expected negative observation; do
not turn it into a success with `--ignore-status`. If access or topology is
missing, report the run as blocked rather than as a qualification.

## Safety boundary

Do not send configuration commands, clear sessions, change credentials, or
force a tunnel down as part of this workflow. If the user explicitly requests
topology preparation, stop and define the exact mutation, authorization,
rollback, and post-change checks before executing it.
