#!/usr/bin/env python3
"""
Module 09: Troubleshooting -- Python Exercises (Diagnostic Toolkit)

Run with: python3 exercises.py

Covers:
  - DNS resolution check (socket.getaddrinfo)
  - Ping check (subprocess)
  - TCP port check (socket connect)
  - Traceroute (subprocess)
  - Diagnosing common SSH error messages
  - Recommendations based on which check fails
"""

import socket
import subprocess
import sys
import time


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Default target for diagnostics. Change this to test against any host.
DEFAULT_TARGET = "google.com"
DEFAULT_PORT = 443


# ---------------------------------------------------------------------------
# Diagnostic Functions
# ---------------------------------------------------------------------------

def check_dns(hostname: str) -> dict:
    """
    Step 1: DNS Resolution Check

    Tests whether a hostname can be resolved to an IP address.
    This is the very first thing that happens when you type
    'ssh user@hostname' -- the system needs to find the IP.
    """
    result = {
        "check": "DNS Resolution",
        "target": hostname,
        "status": "UNKNOWN",
        "detail": "",
        "ip": None,
    }

    try:
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET)
        if addr_info:
            ip = addr_info[0][4][0]
            result["status"] = "PASS"
            result["ip"] = ip
            result["detail"] = f"Resolved to {ip}"
        else:
            result["status"] = "FAIL"
            result["detail"] = "getaddrinfo returned empty result"
    except socket.gaierror as e:
        result["status"] = "FAIL"
        result["detail"] = f"DNS resolution failed: {e}"
    except Exception as e:
        result["status"] = "FAIL"
        result["detail"] = f"Unexpected error: {e}"

    return result


def check_ping(host: str, count: int = 1, timeout: int = 5) -> dict:
    """
    Step 2: Ping Check (ICMP)

    Tests basic IP-level reachability. Note: many servers and firewalls
    block ICMP, so a failed ping does NOT necessarily mean the host is
    unreachable. Always proceed to the TCP port check even if ping fails.
    """
    result = {
        "check": "Ping (ICMP)",
        "target": host,
        "status": "UNKNOWN",
        "detail": "",
    }

    try:
        # macOS uses -W (milliseconds), Linux uses -W (seconds)
        if sys.platform == "darwin":
            cmd = ["ping", "-c", str(count), "-W", str(timeout * 1000), host]
        else:
            cmd = ["ping", "-c", str(count), "-W", str(timeout), host]

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 5,
        )

        if proc.returncode == 0:
            # Extract round-trip time from output
            for line in proc.stdout.splitlines():
                if "time=" in line or "round-trip" in line or "rtt" in line:
                    result["detail"] = line.strip()
                    break
            if not result["detail"]:
                result["detail"] = "Ping succeeded"
            result["status"] = "PASS"
        else:
            result["status"] = "WARN"
            result["detail"] = "Ping failed (host may block ICMP -- not necessarily down)"

    except FileNotFoundError:
        result["status"] = "WARN"
        result["detail"] = "ping command not found"
    except subprocess.TimeoutExpired:
        result["status"] = "WARN"
        result["detail"] = "Ping timed out (host may block ICMP)"
    except Exception as e:
        result["status"] = "FAIL"
        result["detail"] = f"Unexpected error: {e}"

    return result


def check_tcp_port(host: str, port: int, timeout: int = 5) -> dict:
    """
    Step 3: TCP Port Check

    Tests whether a specific TCP port is open and accepting connections.
    This is the most important check -- if DNS resolves and ping fails
    but the TCP port is open, the service is reachable.

    'Connection refused' = port is closed (nothing listening)
    'Connection timed out' = firewall is silently dropping packets
    """
    result = {
        "check": f"TCP Port {port}",
        "target": f"{host}:{port}",
        "status": "UNKNOWN",
        "detail": "",
    }

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        start = time.time()
        error_code = sock.connect_ex((host, port))
        elapsed = time.time() - start
        sock.close()

        if error_code == 0:
            result["status"] = "PASS"
            result["detail"] = f"Port {port} is open (connected in {elapsed:.2f}s)"
        else:
            result["status"] = "FAIL"
            # Decode common error codes
            if error_code == 61 or error_code == 111:
                result["detail"] = f"Connection refused (error {error_code}) -- nothing listening on port {port}"
            elif error_code == 60 or error_code == 110:
                result["detail"] = f"Connection timed out (error {error_code}) -- likely a firewall dropping packets"
            else:
                result["detail"] = f"Connection failed with error code {error_code}"

    except socket.timeout:
        result["status"] = "FAIL"
        result["detail"] = f"Connection timed out after {timeout}s -- likely a firewall silently dropping packets"
    except socket.gaierror as e:
        result["status"] = "FAIL"
        result["detail"] = f"Could not resolve host: {e}"
    except Exception as e:
        result["status"] = "FAIL"
        result["detail"] = f"Unexpected error: {e}"

    return result


def check_traceroute(host: str, max_hops: int = 15, timeout: int = 30) -> dict:
    """
    Step 4: Traceroute

    Shows the path packets take to reach the destination. Each line
    is a router (hop) along the way. If hops start showing '* * *',
    that is where packets are being dropped or filtered.
    """
    result = {
        "check": "Traceroute",
        "target": host,
        "status": "UNKNOWN",
        "detail": "",
        "hops": [],
    }

    try:
        cmd = ["traceroute", "-n", "-m", str(max_hops), host]

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        lines = proc.stdout.strip().splitlines()
        # Skip the header line
        hop_lines = [l.strip() for l in lines[1:] if l.strip()]
        result["hops"] = hop_lines[:max_hops]

        if proc.returncode == 0 and hop_lines:
            result["status"] = "PASS"
            result["detail"] = f"Completed in {len(hop_lines)} hops"
        else:
            result["status"] = "WARN"
            result["detail"] = "Traceroute did not reach destination"

    except FileNotFoundError:
        result["status"] = "WARN"
        result["detail"] = "traceroute command not found"
    except subprocess.TimeoutExpired:
        result["status"] = "WARN"
        result["detail"] = f"Traceroute timed out after {timeout}s"
    except Exception as e:
        result["status"] = "FAIL"
        result["detail"] = f"Unexpected error: {e}"

    return result


# ---------------------------------------------------------------------------
# SSH Error Diagnosis
# ---------------------------------------------------------------------------

def diagnose_ssh_error(error_message: str) -> dict:
    """
    Given an SSH error message string, identify the likely cause and
    suggest a fix. This simulates the thought process a sysadmin goes
    through when reading error output.
    """
    error_lower = error_message.lower()

    diagnoses = [
        {
            "pattern": "could not resolve hostname",
            "layer": "DNS (Layer 7 / Step 1)",
            "cause": "The hostname cannot be translated to an IP address.",
            "fix": "Check spelling. Verify DNS with 'dig <hostname>'. Check /etc/resolv.conf.",
        },
        {
            "pattern": "network is unreachable",
            "layer": "Routing (Layer 3 / Step 2)",
            "cause": "No route exists to the destination network.",
            "fix": "Check routing table ('netstat -rn'). Verify default gateway. Check VPN.",
        },
        {
            "pattern": "no route to host",
            "layer": "Routing (Layer 3 / Step 2)",
            "cause": "Route exists to the network but the specific host is unreachable.",
            "fix": "Verify the host IP. Check if a firewall is sending ICMP unreachable.",
        },
        {
            "pattern": "connection timed out",
            "layer": "Firewall (Layer 3-4 / Step 3-4)",
            "cause": "Packets are being silently dropped, likely by a firewall.",
            "fix": "Check security groups, NACLs, and host firewall on both sides.",
        },
        {
            "pattern": "connection refused",
            "layer": "Service (Layer 4 / Step 3)",
            "cause": "The port is closed. sshd is not running or not listening on that port.",
            "fix": "Verify sshd is running ('systemctl status sshd'). Check listening port.",
        },
        {
            "pattern": "permission denied (publickey)",
            "layer": "Authentication (Step 6)",
            "cause": "SSH key was not accepted by the server.",
            "fix": "Check key file (-i), authorized_keys on server, file permissions (600/700).",
        },
        {
            "pattern": "host key verification failed",
            "layer": "Authentication (Step 6)",
            "cause": "Server's host key does not match what is in your known_hosts file.",
            "fix": "If server was rebuilt, remove old entry from ~/.ssh/known_hosts. If unexpected, investigate (possible MITM).",
        },
        {
            "pattern": "connection reset by peer",
            "layer": "Service (Step 7)",
            "cause": "Server actively terminated the connection after TCP connected.",
            "fix": "Check sshd logs on the server. Look for fail2ban blocks or config issues.",
        },
        {
            "pattern": "too many authentication failures",
            "layer": "Authentication (Step 6)",
            "cause": "SSH agent offered too many keys before the right one.",
            "fix": "Use 'ssh -i /path/to/key' to specify the correct key, or add IdentitiesOnly=yes to ssh config.",
        },
        {
            "pattern": "broken pipe",
            "layer": "Connection (Step 3-7)",
            "cause": "Connection was dropped mid-session.",
            "fix": "Check network stability. Add ServerAliveInterval to SSH config. Check server load.",
        },
    ]

    for diag in diagnoses:
        if diag["pattern"] in error_lower:
            return {
                "error": error_message,
                "matched_pattern": diag["pattern"],
                "layer": diag["layer"],
                "cause": diag["cause"],
                "fix": diag["fix"],
            }

    return {
        "error": error_message,
        "matched_pattern": None,
        "layer": "Unknown",
        "cause": "Error not recognized.",
        "fix": "Run 'ssh -vvv user@host' for detailed debug output and examine each line.",
    }


# ---------------------------------------------------------------------------
# Full Diagnostic Run
# ---------------------------------------------------------------------------

def run_diagnostics(hostname: str, port: int = 22, run_traceroute: bool = True) -> None:
    """Run all diagnostic checks against a target host and print results."""

    print(f"  Target: {hostname}:{port}")
    print(f"  {'-' * 60}")
    print()

    results = []

    # Step 1: DNS
    dns_result = check_dns(hostname)
    results.append(dns_result)
    print_result(dns_result)

    if dns_result["status"] == "FAIL":
        print()
        print("  >> STOP: DNS resolution failed. Cannot proceed to further checks.")
        print("  >> Recommendation: Verify the hostname is correct. Try:")
        print(f"  >>   dig {hostname}")
        print(f"  >>   nslookup {hostname}")
        print_summary(results)
        return

    resolved_ip = dns_result.get("ip", hostname)
    print()

    # Step 2: Ping
    ping_result = check_ping(resolved_ip)
    results.append(ping_result)
    print_result(ping_result)

    if ping_result["status"] == "WARN":
        print("  >> Note: Ping failure does not mean the host is down.")
        print("  >>       Many servers block ICMP. Continuing to TCP check.")
    print()

    # Step 3: TCP Port
    tcp_result = check_tcp_port(resolved_ip, port)
    results.append(tcp_result)
    print_result(tcp_result)

    if tcp_result["status"] == "FAIL":
        print()
        if "refused" in tcp_result["detail"].lower():
            print(f"  >> DIAGNOSIS: Port {port} is closed (connection refused).")
            print(f"  >> The host is reachable, but nothing is listening on port {port}.")
            print(f"  >> Recommendation: Check if the service is running on the server.")
            print(f"  >>   systemctl status sshd  (or the relevant service)")
            print(f"  >>   sudo lsof -i :{port}")
        elif "timed out" in tcp_result["detail"].lower():
            print(f"  >> DIAGNOSIS: Connection timed out (firewall likely dropping packets).")
            print(f"  >> Recommendation: Check firewalls on BOTH sides:")
            print(f"  >>   - Your outbound rules (can you reach port {port} on other servers?)")
            print(f"  >>   - Server's inbound rules (security groups, NACLs, iptables)")
        print_summary(results)
        return

    print()

    # Step 4: Traceroute (optional, informational)
    if run_traceroute:
        trace_result = check_traceroute(resolved_ip, max_hops=10)
        results.append(trace_result)
        print_result(trace_result)
        if trace_result["hops"]:
            print("  Hops:")
            for hop in trace_result["hops"][:10]:
                print(f"    {hop}")
        print()

    print_summary(results)


def print_result(result: dict) -> None:
    """Print a single check result with color-coded status."""
    status = result["status"]
    if status == "PASS":
        marker = "[PASS]"
    elif status == "WARN":
        marker = "[WARN]"
    elif status == "FAIL":
        marker = "[FAIL]"
    else:
        marker = "[????]"

    print(f"  {marker} {result['check']:<20s} {result['detail']}")


def print_summary(results: list) -> None:
    """Print a summary of all check results."""
    print()
    print(f"  {'=' * 60}")
    print(f"  SUMMARY")
    print(f"  {'=' * 60}")
    for r in results:
        status = r["status"]
        print(f"    [{status:4s}] {r['check']}")

    passed = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)
    print()
    print(f"  {passed}/{total} checks passed.")


# ---------------------------------------------------------------------------
# Exercise: Diagnose SSH Errors
# ---------------------------------------------------------------------------

def exercise_diagnose_errors() -> None:
    print("=" * 70)
    print("EXERCISE: Diagnose Common SSH Error Messages")
    print("=" * 70)
    print()
    print("Given an error message, identify the network layer and suggest a fix.")
    print("This is the skill that separates methodical debugging from guessing.")
    print()

    test_errors = [
        "ssh: Could not resolve hostname db-server.internal: nodename nor servname provided",
        "ssh: connect to host 10.0.0.5 port 22: Connection timed out",
        "ssh: connect to host 10.0.0.5 port 22: Connection refused",
        "Permission denied (publickey).",
        "WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED! Host key verification failed.",
        "ssh: connect to host 10.0.0.5 port 22: Network is unreachable",
        "Connection reset by peer",
        "Received disconnect from 10.0.0.5: Too many authentication failures",
        "Write failed: Broken pipe",
    ]

    for error_msg in test_errors:
        diag = diagnose_ssh_error(error_msg)
        print(f"  Error:  {diag['error']}")
        print(f"  Layer:  {diag['layer']}")
        print(f"  Cause:  {diag['cause']}")
        print(f"  Fix:    {diag['fix']}")
        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print()
    print("###################################################################")
    print("#  Module 09: Troubleshooting -- Diagnostic Toolkit               #")
    print("###################################################################")
    print()

    # Part 1: Run connectivity diagnostics against a real host
    print("=" * 70)
    print("PART 1: Connectivity Diagnostics")
    print("=" * 70)
    print()
    print("Running a series of checks against a target host to demonstrate")
    print("the systematic troubleshooting process. Each check tests a")
    print("different layer of the network stack.")
    print()

    target = DEFAULT_TARGET
    port = DEFAULT_PORT

    # Allow command-line override: python3 exercises.py <host> <port>
    if len(sys.argv) >= 2:
        target = sys.argv[1]
    if len(sys.argv) >= 3:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print(f"  [WARN] Invalid port '{sys.argv[2]}', using {port}")

    run_diagnostics(target, port, run_traceroute=True)
    print()

    # Part 2: SSH error diagnosis
    exercise_diagnose_errors()

    print("=" * 70)
    print("All exercises complete.")
    print()
    print("Key takeaways:")
    print("  - Always diagnose systematically: DNS -> Ping -> Port -> App.")
    print("  - 'Connection timed out' = firewall dropping packets (silent).")
    print("  - 'Connection refused' = port closed, service not running.")
    print("  - 'Permission denied (publickey)' = auth issue, not network.")
    print("  - Use 'ssh -v' for the most detailed SSH debugging info.")
    print()
    print("Usage: python3 exercises.py [hostname] [port]")
    print("  Example: python3 exercises.py my-server.example.com 22")
    print("=" * 70)


if __name__ == "__main__":
    main()
