import exercises.m15.websocket_accept as ex


def test_rfc_6455_example():
    # The canonical example from RFC 6455 §1.3.
    result = ex.ws_accept_key("dGhlIHNhbXBsZSBub25jZQ==")
    print(f"OUTPUT: {result!r}  expected='s3pPLMBiTxaQ9kYGzzhZRbK+xOo='", flush=True)
    assert result == "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="


def test_returns_string():
    result = ex.ws_accept_key("dGhlIHNhbXBsZSBub25jZQ==")
    assert isinstance(result, str), f"Expected str, got {type(result).__name__}"


def test_accept_key_is_base64_of_20_bytes():
    # SHA-1 produces 20 bytes; base64-encoded that's 28 chars ending in "=".
    result = ex.ws_accept_key("dGhlIHNhbXBsZSBub25jZQ==")
    assert len(result) == 28
    assert result.endswith("=")


def test_different_keys_produce_different_accepts():
    a = ex.ws_accept_key("dGhlIHNhbXBsZSBub25jZQ==")
    b = ex.ws_accept_key("YW5vdGhlcl9ub25jZV92YWx1ZQ==")
    assert a != b
