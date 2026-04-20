import exercises.m15.parse_url as ex


def test_http_with_path():
    result = ex.parse_url("http://example.com/path")
    print(f"OUTPUT: {result!r}", flush=True)
    assert result == ("http", "example.com", 80, "/path")


def test_https_explicit_port():
    result = ex.parse_url("https://example.com:8443/")
    assert result == ("https", "example.com", 8443, "/")


def test_wss_default_port():
    result = ex.parse_url("wss://chat.example.com/ws")
    assert result == ("wss", "chat.example.com", 443, "/ws")


def test_ws_default_port():
    result = ex.parse_url("ws://chat.example.com/ws")
    assert result == ("ws", "chat.example.com", 80, "/ws")


def test_missing_path_defaults_to_slash():
    result = ex.parse_url("https://example.com")
    assert result == ("https", "example.com", 443, "/")


def test_http_default_port():
    result = ex.parse_url("http://example.com/")
    assert result == ("http", "example.com", 80, "/")
