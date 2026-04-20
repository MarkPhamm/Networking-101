# Lesson: lessons/m01/01_diagnose_ssh_error.md
# Read the lesson before starting this exercise.

# TASK:
# Implement `error_to_step(msg: str) -> int` which maps an SSH error
# message to the step of the 7-step connection that failed:
#
#   2 — DNS:   "Could not resolve hostname ..."
#   3 — TCP:   "Connection timed out", "Connection refused"
#   5 — KEX:   "REMOTE HOST IDENTIFICATION HAS CHANGED"
#   6 — AUTH:  "Permission denied"
#
# If none of the above match, return 0.
#
# The check should be case-sensitive substring matching — the exact
# phrases above appearing anywhere in `msg`.
#
# TODO: implement the mapping.

def error_to_step(msg: str) -> int:
    # YOUR CODE BELOW
    return 0  # TODO


if __name__ == "__main__":
    samples = [
        "ssh: Could not resolve hostname foo: no address",
        "ssh: connect to host 10.0.0.5 port 22: Connection timed out",
        "ssh: connect to host 10.0.0.5 port 22: Connection refused",
        "@@@ WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED! @@@",
        "mark@host: Permission denied (publickey,password).",
        "something unrelated",
    ]
    for m in samples:
        print(f"step {error_to_step(m)} :: {m}")
