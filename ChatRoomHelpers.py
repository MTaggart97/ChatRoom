from socket import socket


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
