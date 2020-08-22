import socket
import threading
import ClientList
import random

socket.setdefaulttimeout(5)
DISCONNECT = '/disconnect'
DISSCONNECT_MESSAGE = f'To disconnect type: {DISCONNECT}'
client_list = ClientList.ClientList()

def accept_connection(sock: socket):
    """
    Accepts a connection given a socket object. If the connection
    times out, (None, None) is returned.

    Parameters:
        sock (socket): The socket to connect to

    Returns:
        (socket, tuple): A tuple containing the socket object
            and address of the connecting process. Or None, None
            if the connection times out.
    """
    try:
        conn, addr = sock.accept()
    except socket.timeout:
        return (None, None)
    # TODO: The name and chat room could be determined in the protocol
    client_list.addToList(conn,
                          "User" + str(random.randint(0, 1000)),
                          "General")
    conn.sendall(DISSCONNECT_MESSAGE.encode())
    return (conn, addr)


def handle_client(conn: socket, addr: tuple):
    """
    Handles the client connection in a separate thread to the one that
    accepts the connection. This thread will be responsible for processing
    what the client sends.

    Parameter:
        conn (socket): The socket that the connection is using
        addr (tuple) : The host and port tuple

    Returns:
        None
    """
    print(f'[NEW CONNECTION] {addr} has connected')

    connected = True
    while connected:
        try:
            msg = conn.recv(1024).decode()

            current_chat_room = client_list.getConnRoom(conn)
            send_list = client_list.connectionsInRoom(current_chat_room)
            send_list.remove(conn)
            for c in send_list:
                c.sendall(f'{client_list.getName(conn)}: {msg}'.encode())
            # Note that the disconnect message is sent before actually
            # disconnection. This is just a handy way to notify all
            # other users in a room that someone has left
            if msg == DISCONNECT:
                connected = False
                print(f'[DISCONNECTION] {addr} has disconnected')
                # Note minus two as currnet thread is yet to close
                print(f'[CONNECTIONS] There are {threading.activeCount() - 2}'
                      ' connections')
                client_list.removeFromList(conn)
                conn.close()
        except socket.timeout:
            # Ignore timeouts
            pass


def send_help():
    """
    Returns the help message that tells the client how to use this
    chat room.

    Returns:
        (str): The help message
    """
    help_message = ('Welcome to ChatRooms. The following commands'
                    'are currently supported:\n')
    help_message += DISSCONNECT_MESSAGE

    return help_message

# Starts the server. Listens on the socket then awaits connections
def main(addr: tuple):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(addr)
    sock.listen()
    print(f'[STARTING] Server has started and is listening on {addr}')
    try:
        # Loops forever waiting from connections
        while True:
            conn, addr = accept_connection(sock)
            if conn:
                thread = threading.Thread(target=handle_client,
                                          args=(conn, addr))
                thread.start()
                # Minus one to ignore main thread
                print(f'[CONNECTIONS] There are {threading.activeCount() - 1}'
                      ' connections')
    except KeyboardInterrupt:
        print('[EXITING] Keyboard interrupt detected')
    finally:
        sock.close()


if __name__ == '__main__':
    host = 'localhost'
    port = 5000
    addr = (host, port)

    main(addr)
