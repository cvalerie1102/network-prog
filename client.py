import socket
import sys
import time

def main():
    # Check for command-line arguments
    if len(sys.argv) != 3:
        print("Usage: python client.py <hostname> <port>")
        sys.exit(1)

    hostname = sys.argv[1]
    port = int(sys.argv[2])

    # Create a UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(1)  # Set a 1-second timeout for responses

    server_address = (hostname, port)
    print(f"Client running, sending PINGs to {hostname}:{port}")

    for i in range(1, 11):  # Send 10 PING messages
        try:
            message = b'PING'
            print(f"{i} : sent PING...", end=' ')
            client_socket.sendto(message, server_address)  # Send the message to the server

            # Wait for the response
            data, _ = client_socket.recvfrom(1024)
            print(f"received {data}")
        except socket.timeout:
            print("Timed Out")

    client_socket.close()

if __name__ == "__main__":
    main()
