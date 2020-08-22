import socket

host = 'localhost'
port = 5000
addr = (host, port)
DISCONNECT = '/disconnect'

# Connect to the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(addr)
# Server sends initial message describing the chat room
data = s.recv(1024)
print(str(data))

def main():
    connected = True
    # While connected, read user input and send to the server
    while connected:
        userInput = input()
        s.sendall(userInput.encode())
        if userInput == DISCONNECT:
            connected = False


if __name__ == '__main__':
    main()
