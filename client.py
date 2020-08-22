import socket
import threading
from threading import active_count

host = 'localhost'
port = 5000
addr = (host, port)
DISCONNECT = '/disconnect'

# Connect to the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(addr)
# Server sends initial message describing the chat room
# data = s.recv(1024)
# print(data.decode())


def handle_send():
    """
    This is run in it's own thread to send messages to the server.
    It waits for user input, then sends the message on hitting the
    Enter key. This is a blocking action which is why it is in it's
    own thread.
    """
    connected = True
    # While connected, read user input and send to the server
    while connected:
        userInput = input()
        s.sendall(userInput.encode())
        if userInput == DISCONNECT:
            connected = False
    s.close()


def handle_recv():
    """
    This function runs in it's own thread. It runs a blocking call
    to recieve data from the server (messages from other users). This
    call fails when the socket is closed, which happens in the other
    thread.
    """
    while True:
        try:
            data = s.recv(1024)
            print(data.decode())
        except ConnectionAbortedError:
            break
        except OSError:
            break


def main():
    thread_send = threading.Thread(target=handle_send)
    thread_send.start()
    thread_recv = threading.Thread(target=handle_recv)
    thread_recv.start()


if __name__ == '__main__':
    main()
