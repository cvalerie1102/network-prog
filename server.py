import socket
import sys
import random

def main():
    # Check for command-line arguments
    if len(sys.argv) != 2:
        print("Usage: python server.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])

    # Create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("", port))  # Bind to localhost and specified port
    print(f"[server] : ready to accept data on port {port}...")

    while True:
        try:
            # Receive message from client
            data, client_address = server_socket.recvfrom(1024)
            message = data.decode("utf-8")
            print(f"[client] : {message}")

            # Randomly decide whether to drop the packet or send a response
            if random.random() < 0.3:  # 30% chance to drop the packet
                print("[server] : packet dropped")
            else:
                response = b'PONG'
                server_socket.sendto(response, client_address)
                print("[server] : PONG sent")
        except KeyboardInterrupt:
            print("\n[server] : shutting down...")
            break
        except Exception as e:
            print(f"[server] : error occurred - {e}")

if __name__ == "__main__":
    main()
