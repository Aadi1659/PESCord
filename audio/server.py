import pyaudio
import socket
import threading
import random

HOST = 'localhost'
PORT = 12336

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket.bind((HOST, PORT))

server_socket.listen(5)

# Define audio parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024

clients = []
active_calls = {}

def broadcast(message, sender):
    for client_socket, client_name, client_address in clients:
        if client_socket != sender:
            client_socket.send(message)

def remaining_clients(sender):
    for client_socket, client_name,client_address in clients:
        if client_socket != sender:
            message = f"Number of remaining clients = {len(clients)-1}"
            client_socket.send(message.encode())

def handle_client(client_socket, client_address):
    client_socket.send(b"Welcome to PESCord Audio Room!\n")
    
    # Prompt the client to enter their name
    client_socket.send(b"Enter your name: ")
    client_name = client_socket.recv(1024).decode().strip()

    # Add the client socket to the list of connected clients
    clients.append((client_socket, client_address, client_name))

    # Broadcast a message to all other clients that a new client has joined
    message = f"{client_name} has joined the chat!".encode()
    broadcast(message, client_socket)

    # Loop to handle audio call requests
    while True:
        try:
            # Prompt the client to enter a command
            client_socket.send(b"\nType 'call <recipient_name>' to start an audio call, or 'exit' to quit.\n")
            command = client_socket.recv(1024).decode().strip()

            # Parse the command and validate it
            if command.startswith("call "):
                recipient_name = command[5:]
                recipient = next((client for client in clients if client[2] == recipient_name), None)
                if recipient is None:
                    raise ValueError(f"No client with name '{recipient_name}' found")
                elif recipient[0] == client_socket:
                    raise ValueError("Cannot call yourself")

                # Generate a random port number for the call
                port_number = random.randint(5000, 9999)

                # Send a message to the recipient to accept the call
                message = f"{client_name} is calling you. Type 'accept {port_number}' to accept the call.".encode()
                recipient[0].send(message)

                # Wait for the recipient to accept the call
                response = recipient[0].recv(1024).decode()
                if response != f"accept {port_number}":
                    raise ValueError("Call rejected by recipient")

                # Start the audio call
                handle_audio_call(client_socket, client_name, recipient[0], recipient_name, port_number)

            elif command == "exit":
                break

            else:
                raise ValueError("Invalid command")

        except Exception as e:
            client_socket.send(str(e).encode())
            break

    # Remove the client socket from the list of connected clients
    clients.remove((client_socket, client_address, client_name))

    # Broadcast a message to all other clients that the client has left
    message = f"{client_name} has left the chat.".encode()
    broadcast(message, client_socket)

    # Close the client socket
    client_socket.close()


def handle_audio_call(sender_socket, sender_name, recipient_socket, recipient_name, port_number):
    # Create a PyAudio object
    p = pyaudio.PyAudio()

    # Open a new microphone stream for the sender
    sender_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    # Open a new speaker stream for the recipient
    recipient_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True)

    # Connect to the recipient's socket
    recipient_socket.connect(('localhost', port_number))

    # Add the sender's socket to the list of active calls
    active_calls[sender_socket] = recipient_socket
    active_calls[recipient_socket] = sender_socket

    # Send a message to the sender that the call has started
    message = f"Audio call started with {recipient_name} on port {port_number}".encode()
    sender_socket.send(message)

    while True:
        try:
            # Receive audio data from the sender
            data = sender_stream.read(CHUNK)

            # If no data is received, assume the sender has disconnected
            if not data:
                raise Exception("Sender disconnected")

            # Play the audio data for the recipient
            recipient_stream.write(data)

        except:
            # If an exception is raised, assume the call has ended
            message = f"Audio call with {recipient_name} has ended.".encode()
            sender_socket.send(message)
            recipient_socket.send(message)

            # Close the streams and remove the sockets from the list of active calls
            sender_stream.close()
            recipient_stream.close()
            del active_calls[sender_socket]
            del active_calls[recipient_socket]

            # Send a message in the server 
            print(f"Audio call ended between {sender_name} and {recipient_name}")
            break

    # Terminate the PyAudio object
    p.terminate()


print(f"Server listening on {HOST}:{PORT}")

while True:
    # Accept incoming connections
    client_socket, client_address = server_socket.accept()

    # Spawn a new thread to handle the connection
    client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
    client_thread.start()

