# Exercise: Parse an SSH public key line

The file `~/.ssh/authorized_keys` is just a text file, one public key
per line. Each line has three whitespace-separated fields:

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx mark@work
└── type ─┘ └──────────────── base64 key material ──────────────────┘ └ comment ┘
```

- **type** — algorithm name. Common values: `ssh-ed25519`, `ssh-rsa`,
  `ecdsa-sha2-nistp256`.
- **key** — base64-encoded public key bytes. One long blob, no spaces
  inside.
- **comment** — free-form label. Often `user@host` but can be anything,
  including multi-word strings.

This is the exact format SSH reads to decide whether to let you in.

## What to do

1. Open `exercises/m02/inspect_pubkey.py`.
2. Implement `parse_pubkey(line)` returning `(type, key, comment)`.
3. Handle lines with no comment (return `""`).
4. Press `v`.

## Why this is worth doing

Parsing this format yourself demystifies `authorized_keys`. Next time
you audit a server's keys or push a key via cloud-init or Terraform,
you'll recognize what you're looking at — three fields, separated by
spaces, comment optional.
