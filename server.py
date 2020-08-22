import socket
import threading

socket.setdefaulttimeout(5)
DISCONNECT = '/disconnect'
CONN_MESSAGE = f'Connected to server. To disconnect type: {DISCONNECT}'

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
    print('Connection made from', addr)
    conn.sendall(CONN_MESSAGE.encode())
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
    conn.sendall(CONN_MESSAGE.encode())
    print(f'[NEW CONNECTION] {addr} has connected')

    connected = True
    while connected:
        try:
            msg = conn.recv(1024).decode()
            if msg == DISCONNECT:
                connected = False

            print(f'{addr} {msg}')
        except socket.timeout:
            # Ignore timeouts
            pass


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
                print(f'[CONNECTIONS] There are {threading.activeCount() -1}'
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
