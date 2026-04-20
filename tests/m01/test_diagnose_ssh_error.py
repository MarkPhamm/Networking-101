import exercises.m01.diagnose_ssh_error as ex


def test_dns_failure_is_step_2():
    msg = "ssh: Could not resolve hostname foo: no address"
    result = ex.error_to_step(msg)
    print(f"OUTPUT: {result} for DNS failure", flush=True)
    assert result == 2


def test_tcp_timeout_is_step_3():
    result = ex.error_to_step("ssh: connect to host 10.0.0.5 port 22: Connection timed out")
    assert result == 3


def test_tcp_refused_is_step_3():
    result = ex.error_to_step("ssh: connect to host 10.0.0.5 port 22: Connection refused")
    assert result == 3


def test_host_key_change_is_step_5():
    result = ex.error_to_step("@@@ WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED! @@@")
    assert result == 5


def test_permission_denied_is_step_6():
    result = ex.error_to_step("mark@host: Permission denied (publickey,password).")
    assert result == 6


def test_unrecognized_is_zero():
    result = ex.error_to_step("some completely unrelated line")
    assert result == 0
