from queue import Queue
import random
import socket
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
from ChatRoomHelpers import ClientSetUp, MessageProtocol as mp

host = socket.gethostbyname(socket.gethostname())
port = 5000
addr = (host, port)
DISCONNECT = '/disconnect'  # Disconnect message
NAME = ''                   # Name of this client

# Setup connection to the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

msgRcvQueue = Queue()   # FIFO Queue
window = tk.Tk()        # Main window
frame = tk.Frame()      # Frame containing history of messages

def checkForMessages():
    """
    Checks the msgRcvQueue for messages. If there is a message in the
    queue, get it and create a label with the message in it. Message is
    removed once it is used.
    """
    if not msgRcvQueue.empty():
        label = tk.Label(text=msgRcvQueue.get(), master=frame)
        label.pack()
    window.after(100, checkForMessages)

def setUpWindow():
    """
    Populates the window that the user will use to send and
    recieve messages. Consists of a frame full of labels that is used to
    show the messages. A text box to type messages and a send button.

    Parameters:
        window (tkinter): The window to display
    """
    input_box = tk.Text()
    button = tk.Button(text="Send")
    # Using a lambda here so that the inputBox can be passed in as
    # and argument
    button.bind("<Button-1>",
                lambda event, inputBox=input_box:
                    handle_send(inputBox))

    frame.pack()
    input_box.pack()
    button.pack()

    window.protocol("WM_DELETE_WINDOW", on_close)
    window.after(0, checkForMessages)


def handle_send(input_box: tk.Text):
    """
    Executed when the user presses send. It will get and clear the
    text box then send the message. The message will be put straight
    into the list of messages on the client side. This is done so that
    the message doesn't need to be sent to the server and back again.

    If the server cannot be contacted, a message is displayed to the
    user to restart.

    Parameter:
        input_box (tk.Text): Text box containing the message
    """
    msg = input_box.get("1.0", tk.END).rstrip()
    input_box.delete("1.0", tk.END)
    try:
        mp.send_msg_protocol(s, msg, NAME)
        # Create a label with the clients message and add it to the frame
        label = tk.Label(text='You: ' + msg, master=frame)
        label.pack()
        if msg == DISCONNECT:
            window.destroy()
            s.close()
    except ConnectionAbortedError:
        msgRcvQueue.put('Lost connection with server, please restart')
    except OSError:
        msgRcvQueue.put('Lost connection with server, please restart')


def on_close():
    """
    Funciton to handle when the user closes the window instead of typing
    the DISCONNECT message. First notifies the server that you are
    disconnecting, then closes the socket and window. If the socket was already
    closed (say by the server), then simply destroy the window.
    """
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        try:
            mp.send_msg_protocol(s, DISCONNECT, NAME)
            s.close()
        except ConnectionAbortedError:
            pass
        except OSError:
            pass
        finally:
            window.destroy()


def handle_recv():
    """
    This function runs in it's own thread. It runs a blocking call
    to recieve data from the server (messages from other users). This
    call fails when the socket is closed, which happens in the other
    thread.
    """
    while True:
        try:
            data = mp.recv_msg_protocol(s)
            # Ignore if data is empty or the header was invalid
            if data:
                msgRcvQueue.put(data)
        except ConnectionAbortedError:
            break
        except OSError:
            break


def main():
    connected = False
    dialog = ClientSetUp()
    window.protocol("WM_DELETE_WINDOW", dialog.on_close)
    window.mainloop()
    NAME, ip, port = (dialog.name, dialog.ip, dialog.port)
    while not connected:
        try:
            port = int(port)
            addr = (ip, port)
            s.connect(addr)
            connected = True
        except ConnectionRefusedError:
            dialog.retry(name=NAME)
            NAME, ip, port = (dialog.name, dialog.ip, dialog.port)
        except ValueError:
            dialog.retry(name=NAME, ip=ip)
            NAME, ip, port = (dialog.name, dialog.ip, dialog.port)
        except Exception:
            # Assume all other exceptions are because of failed connection
            dialog.retry(name=NAME)
            NAME, ip, port = (dialog.name, dialog.ip, dialog.port)
    dialog.destroy()

    thread_recv = threading.Thread(target=handle_recv)
    thread_recv.start()
    setUpWindow()

    if not NAME:
        # If name was not entered, create a random name
        NAME = "User" + str(random.randint(0, 1000))

    # Send the first message that initialises the connection.
    # This simply involves setting the name of this client on the server.
    try:
        mp.send_msg_protocol(s, NAME, NAME)
    except Exception:
        # If this fails, the initialisation failed so client is not
        # connected to server properly
        msgRcvQueue.put('Connection not set up properlly, restart application')

    window.mainloop()


if __name__ == '__main__':
    main()
