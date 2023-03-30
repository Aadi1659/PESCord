import socket
import threading

def receive_messages(client_socket):
    while True:
        # Check if the socket is still open
        if client_socket.fileno() == -1:
            return

        # Receive incoming messages from the server
        data = client_socket.recv(1024)
        if not data:
            break
        print(data.decode())

def send_message(client_socket):
    while True:
        # get user input
        message = input()

        # send the message to the server
        client_socket.sendall(message.encode())

# create a TCP/IP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# connect the socket to the server's IP address and port
server_address = ('192.168.70.62', 12337)
client_socket.connect(server_address)

# start a new thread to receive messages from the server
receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
receive_thread.start()

# start a new thread to send messages to the server
send_thread = threading.Thread(target=send_message, args=(client_socket,))
send_thread.start()