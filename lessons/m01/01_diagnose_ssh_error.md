# Exercise: Map an SSH error to the step that failed

Module 00 showed the 7-step SSH connection. Module 01 listed the
common failure modes. The single most useful skill is mapping an
error message back to the step that broke.

| Error substring | Step | Meaning |
|---|---|---|
| `Could not resolve hostname` | 2 | DNS lookup failed |
| `Connection timed out` | 3 | TCP SYN went nowhere |
| `Connection refused`   | 3 | Reached the host, nothing on port 22 |
| `REMOTE HOST IDENTIFICATION HAS CHANGED` | 5 | Host key mismatch |
| `Permission denied` | 6 | Authentication failed |

## What to do

1. Open `exercises/m01/diagnose_ssh_error.py`.
2. Implement `error_to_step(msg: str) -> int` with case-sensitive
   substring matching against the phrases above. Return `0` for
   anything unrecognized.
3. Press `v`.

## Why this exercise exists

Next time SSH (or any TCP service) fails you'll scan the error for
these keywords and jump straight to the right module. This is how a
5-minute debug becomes a 30-second debug.
