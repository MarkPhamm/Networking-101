import exercises.m02.inspect_pubkey as ex


def test_full_line_with_comment():
    result = ex.parse_pubkey("ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIxxxxxxxxxx mark@work")
    print(f"OUTPUT: {result!r}", flush=True)
    assert result == ("ssh-ed25519", "AAAAC3NzaC1lZDI1NTE5AAAAIxxxxxxxxxx", "mark@work")


def test_no_comment():
    result = ex.parse_pubkey("ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDxxxxx")
    assert result == ("ssh-rsa", "AAAAB3NzaC1yc2EAAAADAQABAAABgQDxxxxx", "")


def test_comment_contains_spaces():
    result = ex.parse_pubkey("ssh-ed25519 AAAAkey mark on work laptop")
    assert result == ("ssh-ed25519", "AAAAkey", "mark on work laptop")


def test_strips_surrounding_whitespace():
    result = ex.parse_pubkey("   ssh-ed25519 AAAAkey mark@work\n")
    assert result == ("ssh-ed25519", "AAAAkey", "mark@work")


def test_returns_three_strings():
    result = ex.parse_pubkey("ssh-ed25519 AAAA mark")
    assert isinstance(result, tuple) and len(result) == 3
    assert all(isinstance(x, str) for x in result)
