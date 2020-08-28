# ChatRoom in Python

## Summary

The goal of this project is to create a chatroom in python. The main feature will be to create and join multiple chat rooms. The server process should be able to handle multiple client processes. And maintain a table of which client is in which chatroom (possibly multiple). Given the correct ip and port, the client will be able to contact a server on the same local network.

## Server

The `server.py` script contains the server process. When run, you will need to input a free port for the server to listen on. The default port is 5000. It will run on the host got by running `socket.gethostbyname(socket.gethostname())`, which should be the machines ip address on the local network. The server creates a new thread for each client that connects. The thread is terminated when the client disconnects.

## Client

The `client.py` script contains the client process. It uses a GUI created with tkinter. It will first ask the user for a username and the details of the server. The protocol it uses to send messages to the server uses fixed length headers. The header contains the length of the message and the username of the client. The main thread runs the GUI and sending of messages. While another thread waits to receive messages. These messages are then added to a global queue which gets polled by the main thread. If there's a message there, it will appear in the UI and then get removed from the queue.
