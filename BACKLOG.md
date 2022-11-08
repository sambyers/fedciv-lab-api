# Backlog

## Lab Status [DONE]
SE gets lab status: default or configured.
- DNAC [DONE]
- Network Devices [DONE]
- ISE [DONE]
- vManage [DONE]

## Lab Reset [WIP]
SE resets entire lab to default state.
- DNAC [WIP]
- Network Devices [WIP]
- ISE [WIP]
- vManage [WIP]

### Notifications
Send notification of when reset is finished.

## ~~Threading~~
~~Thread another function to keep ISE shell open during reset so we don't block the user session.~~

## Task Queue [DONE]
Use a task queue for lab tasks. This gives us the ability to run multiple tasks in parallel and queue up long running tasks (e.g., resetting ISE).

## CLI [WIP]
SE administers all lab automation via CLI

## Identity
SEs are authenticated and authorized in the system.

## Save lab state
SE saves current state of entire lab.

## Resotre lab state
SE restores state of entire lab from previously saved state.

## Web interface
SE administers all lab automation via a web interface.