# Exercise: Parse an SSH target string

In Module 00 you read about **Step 1** of an SSH connection — the shell
parsing the command. Before `ssh` can do anything, it has to take the
string you typed and split it into the user, host, and port.

In this exercise you'll write that splitter yourself for the simple
`user@host` form.

## The input

You'll get strings like:

- `mark@my-server.example.com`  → user `mark`, host `my-server.example.com`
- `my-server.example.com`       → user `""`, host `my-server.example.com`
- `alice@10.0.0.5`              → user `alice`, host `10.0.0.5`

If there's no `@`, the whole string is the host and the user is empty
(SSH falls back to your local `$USER`).

## What to do

1. Open `exercises/m00/parse_ssh_command.py`.
2. Implement `parse_user_host(s: str) -> tuple[str, str]`.
3. Press `v` in `net-learn` to run the tests.

## DE analogy

Same thing the JDBC driver does when you hand it
`jdbc:postgresql://admin:secret@db.example.com:5432/analytics` — it
pulls the user, password, host, port, and database out of the URL
before it even opens a socket.
