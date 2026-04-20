import exercises.m00.parse_ssh_command as ex


def test_user_at_host():
    result = ex.parse_user_host("mark@my-server.com")
    print(f"OUTPUT: parse_user_host('mark@my-server.com') -> {result!r}", flush=True)
    assert result == ("mark", "my-server.com"), (
        f"Expected ('mark', 'my-server.com'), got {result!r}"
    )


def test_host_only():
    result = ex.parse_user_host("my-server.com")
    print(f"OUTPUT: parse_user_host('my-server.com') -> {result!r}", flush=True)
    assert result == ("", "my-server.com"), (
        f"Expected ('', 'my-server.com'), got {result!r}"
    )


def test_user_at_ip():
    result = ex.parse_user_host("alice@10.0.0.5")
    assert result == ("alice", "10.0.0.5"), (
        f"Expected ('alice', '10.0.0.5'), got {result!r}"
    )


def test_returns_tuple_of_two_strings():
    result = ex.parse_user_host("bob@host")
    assert isinstance(result, tuple) and len(result) == 2
    assert all(isinstance(x, str) for x in result)
