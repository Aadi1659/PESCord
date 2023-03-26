import socket
import threading

# Choose a host and port for the server to listen on
HOST = 'localhost'
PORT = 12337

# Create a socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the host and port
server_socket.bind((HOST, PORT))

# Listen for incoming connections
server_socket.listen()  

# Store the list of connected clients
clients = []

def broadcast(message,sender,temp_name):
    """
    Broadcasts a message to all connected clients except the sender
    """
    for client_socket,client_name in clients:
        if client_socket != sender:
            client_socket.send(f"{temp_name}: ".encode() + message)

def remaining_clients(sender):
     for client_socket,client_name in clients:
        if client_socket != sender:
            message = f"Number of remaining clients = {len(clients)-1}"
            client_socket.send(message.encode())
            
            
def handle_client(client_socket, client_address):
    """
    Handles a single client connection
    """
    client_socket.send(b"Welcome to PESCord!\n")
    client_socket.send(b"You can quit the chat anytime by typing 'quit PESCord' \n(psst its case sensitive!)\n")
    
    # Prompt the client to enter their name
    client_socket.send(b"Enter your name: ")
    client_name = client_socket.recv(1024).decode().strip()

    # Add the client socket to the list of connected clients
    clients.append((client_socket,client_name))

    print(f"New connection from {client_address[0]}:{client_address[1]}, client name: {client_name}")

    # Broadcast a message to all other clients that a new client has joined
    message = f"{client_name} has joined the chat!".encode()
    broadcast(message,client_socket,"SERVER")

    while True:
        temp_name = client_name 
        try:
            # Receive a message from the client
            message = client_socket.recv(1024)

            if not message:
                # If no data is received, assume the client has disconnected
                raise Exception("Client disconnected")

            # Broadcast the message to all other clients
            
            broadcast(message,client_socket,temp_name)

        except:

            # Broadcast a message to all other clients that the client has left
            message = f"{temp_name} has left the chat.".encode()
            broadcast(message,client_socket,"SERVER")
            
            #send message in the server 
            print(f"Connection ended from {client_address[0]}:{client_address[1]}, client name: {client_name}")
            
            remaining_clients(client_socket)
            
            clients.remove((client_socket,client_name))
            
            # Close the client socket
            client_socket.close()
            
                        
            break

print(f"Server listening on {HOST}:{PORT}")

while True:
    # Accept incoming connections
    client_socket, client_address = server_socket.accept()

    # Spawn a new thread to handle the connection
    client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
    client_thread.start()