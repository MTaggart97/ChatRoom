import socket
import threading
from ChatRoomHelpers import ClientList
from ChatRoomHelpers import MessageProtocol as mp
import re
from tabulate import tabulate

socket.setdefaulttimeout(20)

DISCONNECT = '/disconnect'
DISSCONNECT_MESSAGE = f'{DISCONNECT} - To disconnect from server'
HELP = '/help'
HELP_MESSAGE = f'{HELP} - To see this message again'
MOVE_ROOM = '/move'
MOVE_ROOM_MESSAGE = (f'{MOVE_ROOM} Name - To create/move into a'
                     ' room called "Name"')
LEAVE_ROOM = '/leave'
LEAVE_ROOM_MESSAGE = (f'{LEAVE_ROOM} - To leave the current room and move'
                      ' into General room')
ROOM_DETAILS = '/rooms'
ROOM_DETAILS_MESSGAE = f'{ROOM_DETAILS} - To get a list of available rooms'

client_list = ClientList()
DEFAULT_ROOM = "General"
NAME = "SERVER"

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

    try:
        client_name = mp.recv_msg_protocol(conn)
        client_list.addToList(conn,
                              client_name,
                              DEFAULT_ROOM)
        send_help(conn)
        return (conn, addr)
    except socket.timeout:
        # If the user takes too long to respond with a name, close connection
        print(f"[CLOSING] {addr} took too long to respond")
        conn.close()
        return (None, None)


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
    sendMsg(conn, f'{client_list.getName(conn)} has entered the chat')

    connected = True
    while connected:
        try:
            msg = mp.recv_msg_protocol(conn)

            # If msg is not a special message then send to all.
            # Otherwise handle request based on input
            if not msg:
                # Do nothing if header was invalid
                pass
            if msg == HELP:
                send_help(conn)
            elif msg == DISCONNECT:
                connected = False
                disconnect(conn)
            elif re.match(MOVE_ROOM + "*", msg):
                updateRoom(conn, msg)
            elif msg == LEAVE_ROOM:
                leaveRoom(conn)
            elif msg == ROOM_DETAILS:
                sendRoomDetails(conn)
            else:
                sendMsg(conn, msg)

        except socket.timeout:
            # Ignore timeouts
            pass
        except ConnectionResetError:
            # This error can be thrown when the client disconnects
            connected = False
            disconnect(conn)


def sendRoomDetails(conn: socket):
    """
    Sends the list of clients and rooms to the given connection.

    Paramters:
        conn (socket): Connection to send list to
    """
    data = tabulate([list(e.values())[1:] for e in client_list.getList()],
                    headers=client_list.getList()[0].keys())
    mp.send_msg_protocol(conn, data, NAME)


def sendMsg(conn: socket, msg: str):
    """
    Given a connection and message, this will send the message to all
    clients in the chat room (except itself).

    Parameters:
        conn (socket): The client that is sending the message
        msg (str): The message to send
    """
    current_chat_room = client_list.getConnRoom(conn)
    send_list = client_list.connectionsInRoom(current_chat_room)
    send_list.remove(conn)
    if send_list:
        for c in send_list:
            mp.send_msg_protocol(c, f'{client_list.getName(conn)}: {msg}',
                                 NAME)


def disconnect(conn: socket):
    """
    Given a socket, it will remove that socket from the client list and
    close the socket

    Parameters:
        conn (socket): Connection to close
    """
    print(f'[DISCONNECTION] {addr} has disconnected')
    # Note minus two as currnet thread is yet to close
    print(f'[CONNECTIONS] There are {threading.activeCount() - 2}'
          ' connections')
    leaveRoom(conn)
    client_list.removeFromList(conn)
    conn.close()


def send_help(conn: socket):
    """
    Sends the help message to the inputted connection. This message tells
    the user how to use the chat room

    Parmeters:
        conn (socket): The connection to send the message to
    """
    help_message = ('Welcome to ChatRooms. The following commands'
                    'are currently supported:\n')
    help_message += HELP_MESSAGE + '\n'
    help_message += DISSCONNECT_MESSAGE + '\n'
    help_message += MOVE_ROOM_MESSAGE + '\n'
    help_message += LEAVE_ROOM_MESSAGE + '\n'
    help_message += ROOM_DETAILS_MESSGAE + '\n'

    mp.send_msg_protocol(conn, help_message, NAME)


def updateRoom(conn: socket, chat_room: str):
    """
    Leaves the connections current chat romm and changes to another.
    Ensures that the chat room is valid before changing for the given
    connection.

    Parameters:
        conn (socket): The client to update
        chat_room (str): The room to join prepended with {CREATE_ROOM}
    """
    new_room = chat_room[len(MOVE_ROOM):].strip()
    if new_room == client_list.getConnRoom(conn):
        # If you're moving into the same room, do nothing
        pass
    elif not new_room == '':
        leaveRoom(conn)
        client_list.updateChatRoom(conn, new_room)
        sendMsg(conn, f'{client_list.getName(conn)} has entered the chat')
    else:
        msg = f'"{new_room}" is not a valid name.'
        mp.send_msg_protocol(conn, msg, NAME)


def leaveRoom(conn: socket):
    """
    Given a connection, it will leave it's current room and join the
    default room. If this function is called while in the DEFAULT_ROOM,
    it is assumed that you will be leaving it. So no need to send the
    "entered" message if that's the case.
    """
    sendMsg(conn, f'{client_list.getName(conn)} has left the chat')
    # If the client was already in the DEFAULT_ROOM, don't tell others
    # that you have entered (since you were already there).
    if not client_list.getConnRoom(conn) == DEFAULT_ROOM:
        client_list.updateChatRoom(conn, DEFAULT_ROOM)
        sendMsg(conn, f'{client_list.getName(conn)} has entered the chat')


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
