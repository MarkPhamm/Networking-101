#!/usr/bin/env python3
"""
Module 08: The TCP/IP Stack -- Python Exercises

Run with: python3 exercises.py

Covers:
  - Packet encapsulation simulator (Application -> TCP -> IP -> Ethernet)
  - TCP three-way handshake simulation with sequence numbers
  - TCP vs UDP comparison (server/client side by side)
  - De-encapsulation (unwrapping each layer)
  - TCP flags reference
"""

import struct
import socket
import threading
import time
import json


# ---------------------------------------------------------------------------
# Exercise 1: Packet Encapsulation Simulator
# ---------------------------------------------------------------------------

def exercise_1() -> None:
    print("=" * 70)
    print("EXERCISE 1: Packet Encapsulation Simulator")
    print("=" * 70)
    print()
    print("When you type a command over SSH, your keystroke passes through")
    print("every layer of the TCP/IP stack. Each layer wraps the data from")
    print("the layer above with its own header, like putting a letter in an")
    print("envelope, then in a mailer, then in a shipping box.")
    print()

    # Application data
    app_data = "ls -la"
    print(f"  Layer 4 - Application Data:")
    print(f"    Payload: '{app_data}'")
    print(f"    Bytes:   {app_data.encode().hex()}")
    print()

    # TCP header (simplified)
    tcp_header = {
        "src_port": 54321,
        "dst_port": 22,
        "seq_num": 1000,
        "ack_num": 2000,
        "flags": "PSH-ACK",
        "window": 65535,
    }

    # Build a simplified TCP header (20 bytes minimum)
    # src_port(2) + dst_port(2) + seq(4) + ack(4) + offset+flags(2) + window(2) + checksum(2) + urgent(2)
    flag_bits = 0x018  # PSH(0x008) + ACK(0x010)
    data_offset = 5 << 12  # 5 * 4 = 20 bytes, shifted to upper nibble
    tcp_bytes = struct.pack(
        "!HHIIHHH",
        tcp_header["src_port"],
        tcp_header["dst_port"],
        tcp_header["seq_num"],
        tcp_header["ack_num"],
        data_offset | flag_bits,
        tcp_header["window"],
        0,  # checksum placeholder
    )
    # Pad to 20 bytes (urgent pointer)
    tcp_bytes += struct.pack("!H", 0)

    tcp_segment = tcp_bytes + app_data.encode()

    print(f"  Layer 3 - TCP Segment:")
    print(f"    Src Port:    {tcp_header['src_port']}")
    print(f"    Dst Port:    {tcp_header['dst_port']} (SSH)")
    print(f"    Seq Number:  {tcp_header['seq_num']}")
    print(f"    Ack Number:  {tcp_header['ack_num']}")
    print(f"    Flags:       {tcp_header['flags']}")
    print(f"    Window:      {tcp_header['window']}")
    print(f"    Header size: {len(tcp_bytes)} bytes")
    print(f"    Total size:  {len(tcp_segment)} bytes (header + payload)")
    print()

    # IP header (simplified)
    ip_header = {
        "version": 4,
        "ttl": 64,
        "protocol": 6,  # TCP
        "src_ip": "192.168.1.100",
        "dst_ip": "10.0.0.5",
    }

    # Build a simplified IP header (20 bytes)
    src_ip_bytes = socket.inet_aton(ip_header["src_ip"])
    dst_ip_bytes = socket.inet_aton(ip_header["dst_ip"])
    version_ihl = (4 << 4) | 5  # IPv4, 5*4=20 byte header
    total_length = 20 + len(tcp_segment)
    ip_bytes = struct.pack(
        "!BBHHHBBH4s4s",
        version_ihl,
        0,               # DSCP/ECN
        total_length,
        0,               # Identification
        0,               # Flags/Fragment offset
        ip_header["ttl"],
        ip_header["protocol"],
        0,               # Checksum placeholder
        src_ip_bytes,
        dst_ip_bytes,
    )

    ip_packet = ip_bytes + tcp_segment

    print(f"  Layer 2 - IP Packet:")
    print(f"    Version:     IPv{ip_header['version']}")
    print(f"    TTL:         {ip_header['ttl']}")
    print(f"    Protocol:    {ip_header['protocol']} (TCP)")
    print(f"    Src IP:      {ip_header['src_ip']}")
    print(f"    Dst IP:      {ip_header['dst_ip']}")
    print(f"    Header size: {len(ip_bytes)} bytes")
    print(f"    Total size:  {len(ip_packet)} bytes (IP header + TCP segment)")
    print()

    # Ethernet frame (simplified)
    eth_header = {
        "src_mac": "AA:BB:CC:DD:EE:01",
        "dst_mac": "AA:BB:CC:DD:EE:02",
        "ethertype": 0x0800,  # IPv4
    }

    src_mac_bytes = bytes.fromhex(eth_header["src_mac"].replace(":", ""))
    dst_mac_bytes = bytes.fromhex(eth_header["dst_mac"].replace(":", ""))
    eth_bytes = struct.pack(
        "!6s6sH",
        dst_mac_bytes,
        src_mac_bytes,
        eth_header["ethertype"],
    )

    ethernet_frame = eth_bytes + ip_packet

    print(f"  Layer 1 - Ethernet Frame:")
    print(f"    Dst MAC:     {eth_header['dst_mac']}")
    print(f"    Src MAC:     {eth_header['src_mac']}")
    print(f"    EtherType:   0x{eth_header['ethertype']:04X} (IPv4)")
    print(f"    Header size: {len(eth_bytes)} bytes")
    print(f"    Total size:  {len(ethernet_frame)} bytes (complete frame)")
    print()

    print("  --- Encapsulation summary ---")
    print(f"    Application data:   {len(app_data.encode()):>4d} bytes  ('{app_data}')")
    print(f"    + TCP header:       {len(tcp_bytes):>4d} bytes")
    print(f"    + IP header:        {len(ip_bytes):>4d} bytes")
    print(f"    + Ethernet header:  {len(eth_bytes):>4d} bytes")
    print(f"    = Total on wire:    {len(ethernet_frame):>4d} bytes")
    print()
    print("  That tiny 'ls -la' command needed 48 bytes of headers to")
    print("  travel across the network. Each layer adds its own addressing")
    print("  and control information.")
    print()


# ---------------------------------------------------------------------------
# Exercise 2: TCP Three-Way Handshake
# ---------------------------------------------------------------------------

def exercise_2() -> None:
    print("=" * 70)
    print("EXERCISE 2: TCP Three-Way Handshake Simulation")
    print("=" * 70)
    print()
    print("Before any data flows over TCP, the two sides must agree to")
    print("communicate. This is the three-way handshake: SYN -> SYN-ACK -> ACK.")
    print("It establishes initial sequence numbers so both sides can track")
    print("which bytes have been sent and received.")
    print()

    client_isn = 1000   # Client's Initial Sequence Number
    server_isn = 5000   # Server's Initial Sequence Number

    print("  Client: 192.168.1.100:54321")
    print("  Server: 10.0.0.5:22 (SSH)")
    print()

    # Step 1: SYN
    print("  Step 1: Client -> Server  [SYN]")
    print(f"    Flags:       SYN")
    print(f"    Seq:         {client_isn}")
    print(f"    Ack:         0 (not yet acknowledging anything)")
    print(f"    Meaning:     'I want to connect. My starting sequence number is {client_isn}.'")
    print()

    # Step 2: SYN-ACK
    print("  Step 2: Server -> Client  [SYN-ACK]")
    print(f"    Flags:       SYN, ACK")
    print(f"    Seq:         {server_isn}")
    print(f"    Ack:         {client_isn + 1}")
    print(f"    Meaning:     'Got it. My starting sequence number is {server_isn}.")
    print(f"                  I acknowledge your seq {client_isn}, expecting {client_isn + 1} next.'")
    print()

    # Step 3: ACK
    print("  Step 3: Client -> Server  [ACK]")
    print(f"    Flags:       ACK")
    print(f"    Seq:         {client_isn + 1}")
    print(f"    Ack:         {server_isn + 1}")
    print(f"    Meaning:     'Acknowledged. I expect your next byte at seq {server_isn + 1}.'")
    print()

    print("  Connection ESTABLISHED. Both sides now agree on sequence numbers.")
    print()

    # Show data transfer
    print("  --- First data exchange ---")
    data = "SSH-2.0-OpenSSH_8.9"
    data_len = len(data.encode())
    print()
    print(f"  Step 4: Server -> Client  [PSH-ACK] (server banner)")
    print(f"    Seq:         {server_isn + 1}")
    print(f"    Ack:         {client_isn + 1}")
    print(f"    Data:        '{data}' ({data_len} bytes)")
    print(f"    Next seq:    {server_isn + 1 + data_len}")
    print()
    print(f"  Step 5: Client -> Server  [ACK]")
    print(f"    Seq:         {client_isn + 1}")
    print(f"    Ack:         {server_isn + 1 + data_len}")
    print(f"    Meaning:     'I received all {data_len} bytes of your data.'")
    print()

    print("  The sequence numbers track exactly which bytes have been sent")
    print("  and acknowledged. If a segment is lost, the sender knows which")
    print("  bytes to retransmit. This is TCP's reliability guarantee.")
    print()


# ---------------------------------------------------------------------------
# Exercise 3: TCP vs. UDP Comparison
# ---------------------------------------------------------------------------

def exercise_3() -> None:
    print("=" * 70)
    print("EXERCISE 3: TCP vs. UDP -- Side by Side")
    print("=" * 70)
    print()
    print("TCP and UDP are the two main transport protocols. They make very")
    print("different tradeoffs between reliability and speed.")
    print()

    # Comparison table
    features = [
        ("Connection",       "Connection-oriented (handshake)",  "Connectionless (fire and forget)"),
        ("Reliability",      "Guaranteed delivery + ordering",   "No guarantee (best effort)"),
        ("Flow control",     "Yes (sliding window)",             "No"),
        ("Overhead",         "20+ byte header",                  "8 byte header"),
        ("Speed",            "Slower (acknowledgments)",         "Faster (no waiting)"),
        ("Use case",         "SSH, HTTP, database connections",  "DNS, streaming, gaming, logs"),
    ]

    print(f"  {'Feature':<20s} {'TCP':<40s} {'UDP'}")
    print(f"  {'-'*20} {'-'*40} {'-'*38}")
    for feature, tcp, udp in features:
        print(f"  {feature:<20s} {tcp:<40s} {udp}")

    print()

    # Demonstrate with actual sockets (localhost only, no external deps)
    print("  --- Live demo: TCP server/client (localhost) ---")
    print()

    tcp_port = 0  # Let OS pick a free port
    tcp_messages = []

    def tcp_server():
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", 0))
        actual_port = srv.getsockname()[1]
        tcp_messages.append(("port", actual_port))
        srv.listen(1)
        conn, addr = srv.accept()
        data = conn.recv(1024)
        tcp_messages.append(("received", data.decode()))
        conn.sendall(b"TCP ACK: got it")
        conn.close()
        srv.close()

    t = threading.Thread(target=tcp_server, daemon=True)
    t.start()
    time.sleep(0.1)

    # Wait for port
    while not tcp_messages:
        time.sleep(0.01)
    tcp_port = tcp_messages[0][1]

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", tcp_port))
    client.sendall(b"Hello from TCP client")
    reply = client.recv(1024)
    client.close()
    t.join(timeout=2)

    print(f"  TCP client sent:     'Hello from TCP client'")
    if len(tcp_messages) > 1:
        print(f"  TCP server received: '{tcp_messages[1][1]}'")
    print(f"  TCP server replied:  '{reply.decode()}'")
    print(f"  Connection: 3-way handshake -> data exchange -> close")
    print()

    print("  --- Live demo: UDP server/client (localhost) ---")
    print()

    udp_received = []

    def udp_server(port):
        srv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        srv.bind(("127.0.0.1", port))
        srv.settimeout(2)
        try:
            data, addr = srv.recvfrom(1024)
            udp_received.append(data.decode())
            srv.sendto(b"UDP reply: got it", addr)
        except socket.timeout:
            pass
        srv.close()

    # Find a free UDP port
    temp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    temp.bind(("127.0.0.1", 0))
    udp_port = temp.getsockname()[1]
    temp.close()

    t2 = threading.Thread(target=udp_server, args=(udp_port,), daemon=True)
    t2.start()
    time.sleep(0.1)

    udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_client.sendto(b"Hello from UDP client", ("127.0.0.1", udp_port))
    udp_client.settimeout(2)
    try:
        reply_udp, _ = udp_client.recvfrom(1024)
        print(f"  UDP client sent:     'Hello from UDP client'")
        print(f"  UDP server received: '{udp_received[0] if udp_received else '?'}'")
        print(f"  UDP server replied:  '{reply_udp.decode()}'")
    except socket.timeout:
        print("  UDP: no reply (timeout) -- this can happen with UDP!")
    udp_client.close()
    t2.join(timeout=2)

    print(f"  Connection: no handshake, just send the datagram")
    print()
    print("  DE analogy: TCP is like a database transaction with COMMIT/ROLLBACK")
    print("  (guaranteed delivery). UDP is like fire-and-forget log shipping")
    print("  (fast, but some messages may be lost).")
    print()


# ---------------------------------------------------------------------------
# Exercise 4: De-encapsulation
# ---------------------------------------------------------------------------

def exercise_4() -> None:
    print("=" * 70)
    print("EXERCISE 4: De-encapsulation (Unwrapping Each Layer)")
    print("=" * 70)
    print()
    print("At the receiving end, the stack strips headers layer by layer,")
    print("from the outermost (Ethernet) to the innermost (Application).")
    print("This is the reverse of encapsulation.")
    print()

    # Build a simulated frame as nested dict (like a real protocol stack)
    frame = {
        "ethernet": {
            "dst_mac": "BB:BB:BB:BB:BB:02",
            "src_mac": "AA:AA:AA:AA:AA:01",
            "ethertype": "0x0800 (IPv4)",
            "payload": {
                "ip": {
                    "version": 4,
                    "ttl": 62,
                    "protocol": "6 (TCP)",
                    "src_ip": "192.168.1.100",
                    "dst_ip": "10.0.0.5",
                    "payload": {
                        "tcp": {
                            "src_port": 54321,
                            "dst_port": 22,
                            "seq": 1001,
                            "ack": 5001,
                            "flags": "PSH-ACK",
                            "payload": {
                                "application": {
                                    "data": "ls -la\n",
                                    "protocol": "SSH",
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    # De-encapsulate step by step
    print("  Received frame on the wire. Unwrapping...")
    print()

    # Layer 1: Ethernet
    eth = frame["ethernet"]
    print("  [Layer 1] Ethernet Frame")
    print(f"    Dst MAC:    {eth['dst_mac']}  <- Is this my MAC? Yes, accept.")
    print(f"    Src MAC:    {eth['src_mac']}")
    print(f"    EtherType:  {eth['ethertype']}  <- Next layer is IP")
    print(f"    Action:     Strip Ethernet header, pass payload up to IP layer")
    print()

    # Layer 2: IP
    ip = eth["payload"]["ip"]
    print("  [Layer 2] IP Packet")
    print(f"    Version:    IPv{ip['version']}")
    print(f"    TTL:        {ip['ttl']}  (started at 64, decremented by 2 routers)")
    print(f"    Protocol:   {ip['protocol']}  <- Next layer is TCP")
    print(f"    Src IP:     {ip['src_ip']}")
    print(f"    Dst IP:     {ip['dst_ip']}  <- Is this my IP? Yes, accept.")
    print(f"    Action:     Strip IP header, pass payload up to TCP layer")
    print()

    # Layer 3: TCP
    tcp = ip["payload"]["tcp"]
    print("  [Layer 3] TCP Segment")
    print(f"    Src Port:   {tcp['src_port']}")
    print(f"    Dst Port:   {tcp['dst_port']}  <- Which application? SSH (port 22)")
    print(f"    Seq:        {tcp['seq']}")
    print(f"    Ack:        {tcp['ack']}")
    print(f"    Flags:      {tcp['flags']}  <- Data present, acknowledged")
    print(f"    Action:     Strip TCP header, deliver payload to SSH application")
    print()

    # Layer 4: Application
    app = tcp["payload"]["application"]
    print("  [Layer 4] Application Data")
    print(f"    Protocol:   {app['protocol']}")
    print(f"    Data:       '{app['data'].strip()}'")
    print(f"    Action:     SSH server executes the command")
    print()

    print("  De-encapsulation complete. Each layer only reads its own header")
    print("  and passes the rest up. The Ethernet layer does not care about")
    print("  TCP ports, and TCP does not care about MAC addresses. This")
    print("  separation of concerns is what makes the stack composable.")
    print()


# ---------------------------------------------------------------------------
# Exercise 5: TCP Flags Reference
# ---------------------------------------------------------------------------

def exercise_5() -> None:
    print("=" * 70)
    print("EXERCISE 5: TCP Flags and What They Mean")
    print("=" * 70)
    print()
    print("TCP flags are control bits in the TCP header that signal the")
    print("purpose of a segment. They fit in a 6-bit field (some systems")
    print("use 9 bits with ECN flags).")
    print()

    flags = [
        ("SYN", 0x002, "Synchronize",    "Initiates a connection. Carries the initial sequence number.",
         "The 'hello' of the three-way handshake."),
        ("ACK", 0x010, "Acknowledge",     "Confirms receipt of data. The ack field is valid.",
         "Present on almost every segment after the handshake."),
        ("FIN", 0x001, "Finish",          "Sender is done sending data. Initiates connection teardown.",
         "Graceful shutdown -- like closing a file handle."),
        ("RST", 0x004, "Reset",           "Abruptly terminates the connection. Something went wrong.",
         "The 'hang up the phone' signal. Often seen when a port is closed."),
        ("PSH", 0x008, "Push",            "Tells the receiver to deliver data to the app immediately.",
         "Don't buffer -- push it up now. Common with interactive sessions."),
        ("URG", 0x020, "Urgent",          "The urgent pointer field is valid. Rarely used in practice.",
         "Almost never seen in modern applications."),
    ]

    print(f"  {'Flag':<6s} {'Hex':<8s} {'Full Name':<15s} {'Purpose'}")
    print(f"  {'-'*6} {'-'*8} {'-'*15} {'-'*50}")
    for name, val, full, purpose, note in flags:
        print(f"  {name:<6s} 0x{val:03X}   {full:<15s} {purpose}")

    print()
    print("  --- Common flag combinations ---")
    print()

    combos = [
        ("SYN",         "Connection request (step 1 of handshake)"),
        ("SYN-ACK",     "Connection accepted (step 2 of handshake)"),
        ("ACK",         "Acknowledgment (step 3, and most subsequent segments)"),
        ("PSH-ACK",     "Data delivery -- push data to application immediately"),
        ("FIN-ACK",     "Graceful connection close (I'm done sending)"),
        ("RST",         "Connection reset (port closed, error, or firewall reject)"),
        ("RST-ACK",     "Forceful rejection of a connection attempt"),
    ]

    print(f"  {'Flags':<15s} {'Meaning'}")
    print(f"  {'-'*15} {'-'*55}")
    for combo, meaning in combos:
        print(f"  {combo:<15s} {meaning}")

    print()
    print("  When debugging connection issues:")
    print("  - Seeing only SYN with no SYN-ACK? The server or a firewall is")
    print("    not responding. Check if the port is open and the service is running.")
    print("  - Seeing RST? The connection was refused. The port may be closed,")
    print("    or a firewall sent a reject instead of a silent drop.")
    print("  - Seeing FIN from one side? Graceful close. Normal behavior.")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print()
    print("###################################################################")
    print("#  Module 08: The TCP/IP Stack -- Python Exercises                #")
    print("###################################################################")
    print()

    exercise_1()
    exercise_2()
    exercise_3()
    exercise_4()
    exercise_5()

    print("=" * 70)
    print("All exercises complete.")
    print()
    print("Key takeaways:")
    print("  - Encapsulation wraps data with headers at each layer.")
    print("  - De-encapsulation strips headers at the receiving end.")
    print("  - TCP's three-way handshake establishes reliable, ordered delivery.")
    print("  - UDP skips the handshake for speed at the cost of reliability.")
    print("  - TCP flags signal connection state: SYN, ACK, FIN, RST, PSH.")
    print("  - Understanding these layers helps you debug 'connection refused'")
    print("    vs. 'connection timed out' vs. 'connection reset' errors.")
    print("=" * 70)


if __name__ == "__main__":
    main()
