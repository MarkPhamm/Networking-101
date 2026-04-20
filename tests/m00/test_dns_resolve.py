import socket

import pytest

import exercises.m00.dns_resolve as ex


def test_localhost_resolves_to_loopback():
    ip = ex.resolve_ipv4("localhost")
    print(f"OUTPUT: resolve_ipv4('localhost') -> {ip!r}", flush=True)
    assert ip == "127.0.0.1", f"Expected '127.0.0.1', got {ip!r}"


def test_returns_plain_string():
    ip = ex.resolve_ipv4("localhost")
    assert isinstance(ip, str), f"Expected str, got {type(ip).__name__}"
    # Should be a dotted-quad IPv4, four parts, each 0..255.
    parts = ip.split(".")
    assert len(parts) == 4, f"Expected dotted-quad IPv4, got {ip!r}"
    assert all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)


def test_unresolvable_raises_gaierror():
    with pytest.raises(socket.gaierror):
        ex.resolve_ipv4("this-host-does-not-exist.example.invalid")
