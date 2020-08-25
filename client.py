from queue import Queue
import socket
import threading
import tkinter as tk
from tkinter import messagebox

host = 'localhost'
port = 5000
addr = (host, port)
DISCONNECT = '/disconnect'

# Connect to the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(addr)

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

    Parameter:
        input_box (tk.Text): Text box containing the message
    """
    msg = input_box.get("1.0", tk.END).rstrip()
    input_box.delete("1.0", tk.END)
    s.sendall(msg.encode())
    # Create a label with the clients message and add it to the frame
    label = tk.Label(text='You: ' + msg, master=frame)
    label.pack()
    if msg == DISCONNECT:
        s.close()
        window.destroy()

def on_close():
    """
    Funciton to handle when the user closes the window instead of typing
    the DISCONNECT message. First notifies the server that you are
    disconnecting, then closes the socket and window.
    """
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        s.sendall(DISCONNECT.encode())
        s.close()
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
            data = s.recv(1024)
            msgRcvQueue.put(data.decode())
        except ConnectionAbortedError:
            break
        except OSError:
            break


def main():
    thread_recv = threading.Thread(target=handle_recv)
    thread_recv.start()
    setUpWindow()
    window.mainloop()


if __name__ == '__main__':
    main()
