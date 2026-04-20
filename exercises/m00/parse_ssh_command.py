# Lesson: lessons/m00/01_parse_ssh_command.md
# Read the lesson before starting this exercise.

# TASK:
# Write a function `parse_user_host(s: str) -> tuple[str, str]` that
# splits an `ssh`-style target like "mark@my-server.com" into
# (user, host). If the string has no "@", user is "" and the whole
# string is the host.
#
# Examples:
#   parse_user_host("mark@my-server.com")  -> ("mark", "my-server.com")
#   parse_user_host("my-server.com")       -> ("", "my-server.com")
#   parse_user_host("alice@10.0.0.5")      -> ("alice", "10.0.0.5")
#
# TODO: replace the placeholder return with real logic.

def parse_user_host(s: str) -> tuple[str, str]:
    # YOUR CODE BELOW
    return ("", "")  # TODO


if __name__ == "__main__":
    for arg in ["mark@my-server.com", "my-server.com", "alice@10.0.0.5"]:
        print(f"{arg!r:30s} -> {parse_user_host(arg)}")
