# Exercise: Generate an ed25519 SSH key pair

Module 02 covers key-based authentication — the upgrade path from
typing a password every time. An SSH key pair has two files:

- **Private key** (`id_ed25519_learn`) — stays on your machine, mode 600.
- **Public key** (`id_ed25519_learn.pub`) — safe to share; you install
  it into `~/.ssh/authorized_keys` on servers you want to log into.

`ed25519` is the modern default. It's shorter, faster, and as secure
as RSA-4096. Don't use RSA for new keys unless you're forced to by an
old server.

## What to do

Run this **in your terminal**:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_learn -N "" -C "net-learn"
```

- `-t ed25519` — key type
- `-f ~/.ssh/id_ed25519_learn` — output path (avoids clobbering any
  real key you already have)
- `-N ""` — no passphrase (fine for a learning key; **always** set one
  for real keys)
- `-C "net-learn"` — comment; just a label

Then press `v`. The verifier checks:

1. `~/.ssh/id_ed25519_learn` and `.pub` both exist.
2. The private key has mode `600` (owner read/write only).
3. The public key starts with `ssh-ed25519 `.

## Cleanup later

When you're done with this course:

```bash
rm ~/.ssh/id_ed25519_learn ~/.ssh/id_ed25519_learn.pub
```

## DE analogy

SSH keys are to human engineers what IAM access keys are to services
— long-lived credentials that grant access without typing a secret.
The public key is the IAM policy; the private key is the access-key
secret you guard jealously.
