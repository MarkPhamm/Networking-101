# Hints — 02_generate_keypair

## Hint 1
`ssh-keygen -N ""` sets an *empty* passphrase. Without `-N`, `ssh-keygen`
will prompt interactively — and the verifier can't answer prompts.
Use `-N ""` for this exercise.

## Hint 2
If the verifier says the private key isn't mode 600, fix it:

```bash
chmod 600 ~/.ssh/id_ed25519_learn
```

`ssh-keygen` writes 600 by default, but an errant `umask` or a copy
from elsewhere can loosen the permissions.

## Hint 3
If you already have a `~/.ssh/id_ed25519_learn` from a previous attempt
and `ssh-keygen` refuses to overwrite it, delete it first:

```bash
rm ~/.ssh/id_ed25519_learn ~/.ssh/id_ed25519_learn.pub
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_learn -N "" -C "net-learn"
```
