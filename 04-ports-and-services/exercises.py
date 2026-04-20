#!/usr/bin/env python3
"""
Module 04: Ports and Services - Exercises
==========================================
Explore ports, services, and TCP connections: build an echo server,
scan ports, run a mini HTTP server, and observe ephemeral ports.

Run with: python3 exercises.py

No external dependencies required -- stdlib only.
"""

import http.server
import io
import socket
import socketserver
import sys
import threading
import time
import urllib.request


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def banner(title):
    print()
    print("=" * 65)
    print(f"  {title}")
    print("=" * 65)
    print()


def info(msg):
    print(f"  [INFO]  {msg}")


def ok(msg):
    print(f"  [OK]    {msg}")


def warn(msg):
    print(f"  [WARN]  {msg}")


def fail(msg):
    print(f"  [FAIL]  {msg}")


# ---------------------------------------------------------------------------
# Exercise 1: TCP Echo Server and Client
# ---------------------------------------------------------------------------

def exercise1_echo_server():
    """Build a TCP echo server in a thread and communicate with it."""
    banner("EXERCISE 1: TCP Echo Server and Client")

    info("A TCP server listens on a port and accepts connections.")
    info("An echo server sends back whatever the client sends.")
    info("This is the simplest possible networked service.\n")

    # Pick a random high port to avoid conflicts
    port = 0  # Let OS assign a free port

    # Create the server
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(("127.0.0.1", port))
    actual_port = server_sock.getsockname()[1]
    server_sock.listen(1)
    server_sock.settimeout(5)

    ok(f"Echo server listening on 127.0.0.1:{actual_port}")
    info("The server called: socket() -> bind() -> listen()")
    info("It's now waiting for a client to connect.\n")

    # Server thread
    server_received = []

    def server_thread():
        try:
            conn, addr = server_sock.accept()
            info(f"  Server: accepted connection from {addr[0]}:{addr[1]}")
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                server_received.append(data)
                conn.sendall(data)  # Echo back
            conn.close()
        except socket.timeout:
            pass
        except Exception as e:
            fail(f"  Server error: {e}")

    t = threading.Thread(target=server_thread, daemon=True)
    t.start()

    # Client
    print("  CLIENT SIDE:")
    print("  " + "-" * 50)
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_sock.settimeout(3)

    try:
        # Connect
        client_sock.connect(("127.0.0.1", actual_port))
        local = client_sock.getsockname()
        remote = client_sock.getpeername()
        ok(f"Client connected: {local[0]}:{local[1]} -> {remote[0]}:{remote[1]}")
        info(f"Client's ephemeral port: {local[1]} (assigned by OS)")
        print()

        # Send messages
        messages = [
            b"Hello, echo server!",
            b"This is a TCP connection.",
            b"Each message is sent reliably and in order.",
        ]

        for msg in messages:
            client_sock.sendall(msg)
            response = client_sock.recv(1024)
            print(f"    Sent:     {msg.decode()}")
            print(f"    Received: {response.decode()}")
            matches = response == msg
            print(f"    Match:    {'YES (echo works!)' if matches else 'NO (unexpected)'}")
            print()

    except Exception as e:
        fail(f"Client error: {e}")
    finally:
        client_sock.close()

    # Clean up
    server_sock.close()
    t.join(timeout=2)

    info("This is how every TCP service works:")
    info("  1. Server binds to a port and listens")
    info("  2. Client connects (3-way handshake happens)")
    info("  3. Both sides send/receive data")
    info("  4. Either side closes the connection")
    info("")
    info("SSH, HTTP, PostgreSQL, Redis -- they all follow this pattern.")
    info("The only difference is what data they exchange after connecting.")


# ---------------------------------------------------------------------------
# Exercise 2: Port Scanner
# ---------------------------------------------------------------------------

def exercise2_port_scanner():
    """Scan common ports on localhost to see what's running."""
    banner("EXERCISE 2: Port Scanner")

    info("Let's check which common services are running on your machine.")
    info("This is what tools like nmap do (simplified).\n")

    # Common ports and their typical services
    ports_to_check = [
        (22, "SSH", "Remote shell access"),
        (53, "DNS", "Domain name resolution"),
        (80, "HTTP", "Web server (unencrypted)"),
        (443, "HTTPS", "Web server (encrypted)"),
        (3000, "Dev server", "Node.js/Rails dev server"),
        (3306, "MySQL", "MySQL database"),
        (5432, "PostgreSQL", "PostgreSQL database"),
        (5900, "VNC", "Screen sharing"),
        (6379, "Redis", "Redis cache/broker"),
        (8080, "HTTP-alt", "Alternative web server / proxy"),
        (8443, "HTTPS-alt", "Alternative HTTPS"),
        (8888, "Jupyter", "Jupyter notebook"),
        (9090, "Prometheus", "Prometheus metrics"),
        (27017, "MongoDB", "MongoDB database"),
    ]

    open_ports = []
    closed_ports = []

    print(f"  {'Port':<7} {'Service':<14} {'Status':<12} {'Notes'}")
    print(f"  {'-'*7} {'-'*14} {'-'*12} {'-'*30}")

    for port, service, description in ports_to_check:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        try:
            result = sock.connect_ex(("127.0.0.1", port))
            if result == 0:
                status = "OPEN"
                open_ports.append((port, service))

                # Try to grab a banner
                banner_text = ""
                try:
                    sock.settimeout(0.5)
                    data = sock.recv(256)
                    if data:
                        banner_text = data.decode("utf-8", errors="replace").strip()[:30]
                except Exception:
                    pass

                notes = banner_text if banner_text else description
                print(f"  {port:<7} {service:<14} {'** OPEN **':<12} {notes}")
            else:
                status = "closed"
                closed_ports.append((port, service))
                print(f"  {port:<7} {service:<14} {'closed':<12} {description}")
        except Exception as e:
            print(f"  {port:<7} {service:<14} {'error':<12} {e}")
            closed_ports.append((port, service))
        finally:
            sock.close()

    print()
    ok(f"Scan complete: {len(open_ports)} open, {len(closed_ports)} closed")

    if open_ports:
        print()
        info("Open ports found:")
        for port, service in open_ports:
            info(f"  :{port} -> {service} is accepting connections")

    print()
    info("How this works: for each port, we attempt a TCP connect().")
    info("  - Success (0)     -> port is OPEN, something is listening")
    info("  - Refused (61)    -> port is CLOSED, nothing listening")
    info("  - Timeout         -> port is FILTERED (firewall dropping packets)")
    info("")
    info("DE context: If your Spark job can't connect to Postgres on :5432,")
    info("this is the first thing to check -- is the port even open?")


# ---------------------------------------------------------------------------
# Exercise 3: Mini HTTP Server
# ---------------------------------------------------------------------------

def exercise3_http_server():
    """Run a minimal HTTP server and make a request to it."""
    banner("EXERCISE 3: Mini HTTP Server")

    info("HTTP is just a text protocol running over TCP, typically on port 80.")
    info("Let's start a tiny HTTP server and make a request to it.\n")

    # Custom handler that returns educational content
    class ExerciseHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            response = (
                "Hello from Networking 101!\n"
                "\n"
                "You just made an HTTP GET request.\n"
                f"Path requested: {self.path}\n"
                f"Your address: {self.client_address[0]}:{self.client_address[1]}\n"
                f"HTTP version: {self.request_version}\n"
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("X-Module", "04-ports-and-services")
            self.end_headers()
            self.wfile.write(response.encode())

        def log_message(self, format, *args):
            # Suppress default logging
            pass

    # Start server on a random port
    server = socketserver.TCPServer(("127.0.0.1", 0), ExerciseHandler)
    port = server.server_address[1]

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    ok(f"HTTP server running on http://127.0.0.1:{port}")
    print()

    # Make a request using urllib (stdlib)
    try:
        url = f"http://127.0.0.1:{port}/test-page"
        print(f"  Making HTTP GET request to: {url}")
        print()

        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as response:
            status = response.status
            headers = dict(response.getheaders())
            body = response.read().decode("utf-8")

            print(f"  RESPONSE STATUS: {status}")
            print(f"  RESPONSE HEADERS:")
            for key, value in sorted(headers.items()):
                print(f"    {key}: {value}")
            print(f"\n  RESPONSE BODY:")
            for line in body.strip().split("\n"):
                print(f"    {line}")

    except Exception as e:
        fail(f"Request failed: {e}")

    # Now show what HTTP looks like at the raw TCP level
    print()
    print("  " + "-" * 50)
    info("What HTTP looks like at the TCP level:")
    print()

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect(("127.0.0.1", port))

        # Send a raw HTTP request
        raw_request = f"GET /raw-test HTTP/1.0\r\nHost: 127.0.0.1:{port}\r\n\r\n"
        print("  RAW REQUEST (what the client sends over TCP):")
        for line in raw_request.strip().split("\r\n"):
            print(f"    > {line}")
        print()

        sock.sendall(raw_request.encode())

        # Read raw response
        response_data = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response_data += chunk

        print("  RAW RESPONSE (what the server sends back over TCP):")
        for line in response_data.decode("utf-8", errors="replace").split("\r\n")[:10]:
            print(f"    < {line}")

        sock.close()
    except Exception as e:
        fail(f"Raw request failed: {e}")

    # Clean up
    server.shutdown()

    print()
    info("HTTP is just formatted text over TCP. A web browser does exactly")
    info("what we just did: open a TCP connection, send a request, read response.")
    info("HTTPS (port 443) adds TLS encryption, but the HTTP part is the same.")
    info("")
    info("DE context: When your Python script calls requests.get() or")
    info("spark.read.format('jdbc'), it's doing this under the hood --")
    info("TCP connect, send protocol-specific request, read response.")


# ---------------------------------------------------------------------------
# Exercise 4: Ephemeral Ports
# ---------------------------------------------------------------------------

def exercise4_ephemeral_ports():
    """Show how the OS assigns different ephemeral ports for each connection."""
    banner("EXERCISE 4: Ephemeral Ports")

    info("When a client connects, the OS assigns a random 'ephemeral' port")
    info("as the source port. Let's see this in action.\n")

    # Start a simple server
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(("127.0.0.1", 0))
    server_port = server_sock.getsockname()[1]
    server_sock.listen(5)
    server_sock.settimeout(5)

    # Accept connections in a thread
    server_connections = []

    def accept_loop():
        while True:
            try:
                conn, addr = server_sock.accept()
                server_connections.append((conn, addr))
            except (socket.timeout, OSError):
                break

    t = threading.Thread(target=accept_loop, daemon=True)
    t.start()

    # Make several connections and observe the ephemeral ports
    print(f"  Server listening on port {server_port}")
    print(f"  Making 5 connections to observe ephemeral port assignment:\n")

    client_sockets = []
    ephemeral_ports = []

    print(f"  {'Connection':<14} {'Local (you)':<25} {'Remote (server)':<25}")
    print(f"  {'-'*14} {'-'*25} {'-'*25}")

    for i in range(5):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        try:
            sock.connect(("127.0.0.1", server_port))
            local = sock.getsockname()
            remote = sock.getpeername()
            ephemeral_ports.append(local[1])
            print(f"  #{i+1:<13} {local[0]}:{local[1]:<14} {remote[0]}:{remote[1]:<14}")
            client_sockets.append(sock)
        except Exception as e:
            fail(f"Connection {i+1} failed: {e}")

    print()

    if len(ephemeral_ports) >= 2:
        info("Notice how each connection gets a DIFFERENT ephemeral port.")
        info(f"Ports used: {ephemeral_ports}")
        info(f"Port range: {min(ephemeral_ports)} - {max(ephemeral_ports)}")
        print()
        info("The full 'socket pair' that uniquely identifies each connection:")
        for i, port in enumerate(ephemeral_ports):
            print(f"    Connection {i+1}: 127.0.0.1:{port} <-> 127.0.0.1:{server_port}")

    # Clean up
    for sock in client_sockets:
        sock.close()
    server_sock.close()
    t.join(timeout=2)
    for conn, addr in server_connections:
        conn.close()

    print()
    info("Why this matters:")
    info("  - A server port (like :22 or :5432) stays fixed")
    info("  - The client port changes with every connection")
    info("  - The PAIR (source IP:port, dest IP:port) is unique")
    info("  - This is how the OS tracks thousands of connections simultaneously")
    print()
    info("DE context: When your Spark executor opens 50 connections to Postgres,")
    info("each one uses a different ephemeral port on the executor side.")
    info("They all target the SAME server port (5432). The unique pairs let")
    info("the OS keep the data streams separate.")


# ---------------------------------------------------------------------------
# Exercise 5: Connection Refused Deep Dive
# ---------------------------------------------------------------------------

def exercise5_connection_refused():
    """Demonstrate and explain 'Connection Refused' in detail."""
    banner("EXERCISE 5: Understanding 'Connection Refused'")

    info("'Connection refused' is the most common networking error.")
    info("Let's see exactly what it means at the socket level.\n")

    # Scenario 1: Connect to a port with nothing listening
    print("  SCENARIO 1: Connecting to an unused port")
    print("  " + "-" * 50)
    closed_port = 59999

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    try:
        start = time.time()
        sock.connect(("127.0.0.1", closed_port))
        ok("Connected (unexpected)")
    except ConnectionRefusedError:
        elapsed_ms = (time.time() - start) * 1000
        fail(f"ConnectionRefusedError on port {closed_port} ({elapsed_ms:.1f} ms)")
        info("The OS kernel immediately sent back a TCP RST (reset) packet.")
        info("It knows nothing is listening and rejects the connection fast.")
    except Exception as e:
        fail(f"Unexpected error: {e}")
    finally:
        sock.close()

    print()

    # Scenario 2: Start a server, connect, stop server, try again
    print("  SCENARIO 2: Server starts, serves, then stops")
    print("  " + "-" * 50)

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv_port = srv.getsockname()[1]
    srv.listen(1)
    srv.settimeout(2)

    info(f"Started a server on port {srv_port}")

    # Connect while server is running
    client1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client1.settimeout(3)
    try:
        client1.connect(("127.0.0.1", srv_port))
        ok(f"Connection 1: SUCCESS (server is listening on :{srv_port})")
        client1.close()
    except Exception as e:
        fail(f"Connection 1: {e}")
        client1.close()

    # Accept the connection server-side
    try:
        conn, _ = srv.accept()
        conn.close()
    except Exception:
        pass

    # Stop the server
    srv.close()
    info(f"Server on port {srv_port} stopped")

    # Try to connect again
    time.sleep(0.1)  # Brief pause to let port fully close
    client2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client2.settimeout(3)
    try:
        client2.connect(("127.0.0.1", srv_port))
        ok("Connection 2: SUCCESS (unexpected -- port should be closed)")
        client2.close()
    except ConnectionRefusedError:
        fail(f"Connection 2: REFUSED (server is gone, port {srv_port} is closed)")
        info("This is exactly what happens when sshd crashes or PostgreSQL stops.")
    except Exception as e:
        fail(f"Connection 2: {e}")
    finally:
        client2.close()

    print()

    # Summary table
    print("  DIAGNOSTIC GUIDE: What does the error mean?")
    print("  " + "-" * 50)
    print()
    print("    Error                     Meaning")
    print("    -------------------------  ------------------------------------")
    print("    Connection refused         Port closed, nothing listening")
    print("    Connection timed out       Firewall DROP or host unreachable")
    print("    Network unreachable        No route to host (routing problem)")
    print("    Connection reset           Server forcibly closed connection")
    print("    Broken pipe                You wrote to a closed connection")
    print()
    info("Speed of failure is your diagnostic clue:")
    info("  Instant failure (ms)   -> Connection refused (server responded)")
    info("  Slow failure (seconds) -> Timeout (no response at all)")
    info("")
    info("DE context:")
    info("  'Connection refused on :5432' = Postgres isn't running")
    info("  'Connection timed out on :5432' = firewall or wrong IP")
    info("  These are DIFFERENT problems with DIFFERENT fixes.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print()
    print("*" * 65)
    print("  MODULE 04: PORTS AND SERVICES - EXERCISES")
    print("  Building servers, scanning ports, and understanding connections")
    print("*" * 65)

    exercise1_echo_server()
    exercise2_port_scanner()
    exercise3_http_server()
    exercise4_ephemeral_ports()
    exercise5_connection_refused()

    print()
    print("=" * 65)
    print("  KEY TAKEAWAYS")
    print("=" * 65)
    print()
    info("1. Servers bind() to a port and listen(); clients connect()")
    info("2. Port scanning = trying connect() on common ports")
    info("3. HTTP is just formatted text over TCP (GET /path HTTP/1.0)")
    info("4. Each connection gets a unique ephemeral port on the client side")
    info("5. 'Connection refused' = instant, nothing listening")
    info("6. 'Connection timed out' = slow, packets being dropped")
    info("7. The socket pair (src IP:port, dst IP:port) uniquely identifies a connection")
    print()
    info("Next: Module 05 - Subnets and Routing")
    print()


if __name__ == "__main__":
    main()
