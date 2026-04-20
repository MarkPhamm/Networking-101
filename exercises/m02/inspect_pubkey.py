# Lesson: lessons/m02/02_inspect_pubkey.md
# Read the lesson before starting this exercise.

# TASK:
# Implement `parse_pubkey(line: str) -> tuple[str, str, str]` that
# splits a single-line SSH public key into (type, key, comment).
#
# A public-key line looks like:
#
#   ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI...  mark@work
#   └── type ─┘ └──────── key (base64) ────┘  └ comment ┘
#
# Rules:
#   - Exactly one space separates type and key.
#   - The comment is everything after the *second* space, and may itself
#     contain spaces (e.g. "mark on work laptop").
#   - If there is no comment, return "" for it.
#   - Leading/trailing whitespace on `line` should be stripped.
#
# Examples:
#   parse_pubkey("ssh-ed25519 AAAA... mark@work")
#     -> ("ssh-ed25519", "AAAA...", "mark@work")
#   parse_pubkey("ssh-rsa AAAB...")
#     -> ("ssh-rsa", "AAAB...", "")
#
# TODO: replace the placeholder return below.

def parse_pubkey(line: str) -> tuple[str, str, str]:
    # YOUR CODE BELOW
    return ("", "", "")  # TODO


if __name__ == "__main__":
    samples = [
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIExampleBase64Key mark@work",
        "ssh-rsa AAAAB3NzaC1yc2EExampleLongerKey",
        "ssh-ed25519 AAAAC3... mark on work laptop",
    ]
    for s in samples:
        print(f"{s!r}\n  -> {parse_pubkey(s)}\n")
