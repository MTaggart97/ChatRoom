from socket import socket
import json

class ClientList:
    """
    Class to represent the client list that the server maintains
    """
    client_list = []

    def __init__(self):
        self.client_list = []

    def addToList(self, conn: socket, name: str, chat_room: str):
        """
        Adds a connection to the list with the inputted data

        Parameters:
            self (ClientList): This instance
            conn (socket): Connection to client
            name (str): Name of client
            chat_room (str): Chat room that they are in

        Returns:
            (boolean): True if item was successfully added
        """
        temp_dict = {'Connection': conn, 'Name': name, 'Room': chat_room}
        for entry in self.client_list:
            if (entry['Connection'] == conn and entry['Name'] == name
                    and entry['Room'] == chat_room):
                return False
        self.client_list.append(temp_dict)

    def removeFromList(self, conn: socket):
        """
        Removes an item from the list give the connection

        Parmeters:
            self (ClientList): This instance
            conn (socket): Connection to client
        Returns:
            (boolean): True if item was removed successfully
        """
        for entry in self.client_list:
            if entry['Connection'] == conn:
                self.client_list.remove(entry)
                return True
        return False

    def getList(self):
        """
        Returns a copy of the list of clients
        """
        return self.client_list.copy()

    def connectionsInRoom(self, chat_room: str):
        """
        Finds all clients in a give chat room.

        Parameters:
            self (ClientList): This instance
            chat_room (str): Chat room to search for

        Returns:
            (list): A list of connections in that room
        """
        connections = []
        for entry in self.client_list:
            if entry['Room'] == chat_room:
                connections.append(entry['Connection'])
        return connections

    def connections(self):
        """
        Returns a list of all connections.

        Parameters:
            self (ClientList): This instance

        Returns:
            (list): List of all connections
        """
        connections = []
        for entry in self.client_list:
            connections.append(entry['Connection'])
        return connections

    def getConnRoom(self, conn: socket):
        """
        Gets the current room that this connection is in.

        Parameters:
            self (ClientList): This instance
            conn (socket): Connections to search for

        Returns:
            (str): The current chat room of this connection
        """
        for entry in self.client_list:
            if entry['Connection'] == conn:
                return entry['Room']
        return None

    def getName(self, conn: socket):
        """
        Given a socket, return the name of that user.

        Parameters:
            self (ClientList): This instance
            conn (socket): Connections to search for

        Returns:
            (str): The name of the user of that connection
        """
        for entry in self.client_list:
            if entry['Connection'] == conn:
                return entry['Name']
        return None

    def updateChatRoom(self, conn: socket, chat_room: str):
        """
        Given a connection, it will change its chat room

        Parameters:
            self (ClientList): This instance
            conn (socket): The connection to update
            chat_room (str): The chat room to change to

        Returns:
            (boolean): True if client has left the room
        """
        for entry in self.client_list:
            if entry['Connection'] == conn:
                entry['Room'] = chat_room
                return True
        return False

class MessageProtocol:
    """
    Class providing helper functions for the message protocol. Contains the
    header_len variable which is the max length of the header file (8 bytes).

    The protocol uses fixed length headers. A header of lenght 8 bytes is first
    sent. It contains the message length and senders name to the client. The
    message is then sent.
    """
    header_len = 8  # Max length of header in bytes

    def create_header(msg: str, name: str):
        """
        Creates the header for the inputted message.

        Parameters:
            msg (str): The message to be sent
            name (str): The name of the client sending the message

        Returns:
            (str): A json object representing the header for the message

        Errors:
            ValueError: If header lenght is too long
        """
        header_dict = {'content-length': len(msg),
                       'name': name}
        header = json.dumps(header_dict)
        if (len(header) >= 2**MessageProtocol.header_len):
            raise ValueError('Header too large')
        return header

    def parse_header(header: str):
        """
        Parses the header and returns a dictionary representing it.

        Parameters:
            header (str): The header to parse

        Returns:
            (dict): A dictionary representing the header
        """
        return (json.loads(header))

    def send_msg_protocol(conn: socket, msg: str, name: str):
        """
        Function to send the message, including headers. It will first send the
        header for the message. Then sends the actual message.

        Parameters:
            conn (socket): Connection to send message down
            msg (str): Message to send
            name (str): Name of sending process
        """
        header = MessageProtocol.create_header(msg, name).encode()
        header += b' ' * ((2**MessageProtocol.header_len) - len(header))
        conn.sendall(header)           # Send header
        conn.sendall(msg.encode())     # Send message

    def recv_msg_protocol(conn: socket):
        """
        Handles the recieving of messages using the protocol where the
        header is sent first, then the message. Returns nothing if header
        is invalid

        Parameters:
            conn (socket): Socket to recieve message from

        Returns:
            (str): The message sent from socket
        """
        try:
            msg_header = json.loads(conn
                                    .recv(2**MessageProtocol.header_len)
                                    .decode())
            msg = conn.recv(msg_header['content-length']).decode()
            return msg
        except json.decoder.JSONDecodeError:
            # Malformed header, do nothing
            return None
