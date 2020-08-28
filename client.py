from queue import Queue
import random
import socket
import threading
import tkinter as tk
from tkinter import messagebox
from ChatRoomHelpers import ClientSetUp, MessageProtocol as mp

LABEL_WIDTH = 500           # Max width of labels
DISCONNECT = '/disconnect'  # Disconnect message
NAME = ''                   # Name of this client

# Setup connection to the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

msgRcvQueue = Queue()   # FIFO Queue
window = tk.Tk()        # Main window

# Set up scollable frame
baseFrame = tk.Frame(window)
canvas = tk.Canvas(baseFrame)
frame = tk.Frame(canvas)  # Frame containing history of messages


def onFrameConfig(canvas: tk.Canvas):
    """
    Executed when the frame gets larger (i.e. when a messge is sent). It will
    first resize the scroll region. If the user was originally at the
    bottom of the scroll, then they will stay ot the bottom. Otherwise, they
    stay where they are.

    Parameters:
        canvas (Canvas): Canvas widget to configure
    """
    yView = canvas.yview()[1]
    canvas.configure(scrollregion=canvas.bbox('all'))
    if 1 == yView:
        canvas.yview_moveto(1)


def on_mouse_wheel(event, canvas: tk.Canvas):
    canvas.yview_scroll(-1 * int((event.delta) / 120), 'units')


def checkForMessages():
    """
    Checks the msgRcvQueue for messages. If there is a message in the
    queue, get it and create a label with the message in it. Message is
    removed once it is used.
    """
    if not msgRcvQueue.empty():
        label = tk.Label(text=msgRcvQueue.get(),
                         master=frame,
                         justify='left',
                         wraplength=LABEL_WIDTH,
                         relief='raised')
        label.pack(anchor='w')
    window.after(100, checkForMessages)

def setUpWindow():
    """
    Populates the window that the user will use to send and
    recieve messages. Consists of a frame full of labels that is used to
    show the messages. A text box to type messages and a send button.

    Parameters:
        window (tkinter): The window to display
    """
    myscrollbar = tk.Scrollbar(baseFrame, orient="vertical",
                               command=canvas.yview)
    canvas.configure(yscrollcommand=myscrollbar.set)
    canvas.create_window((4, 4), window=frame, anchor="nw")
    frame.bind('<Configure>',
               lambda event, canvas=canvas: onFrameConfig(canvas))

    canvas.bind_all('<MouseWheel>',
                    lambda event, canvas=canvas:
                        on_mouse_wheel(event, canvas))

    input_box = tk.Text(master=window)
    button = tk.Button(master=window, text="Send")
    # Using a lambda here so that the inputBox can be passed in as
    # and argument
    button.bind("<Button-1>",
                lambda event, inputBox=input_box:
                    handle_send(inputBox))

    input_box.bind('<Shift-Return>',
                   lambda event, inputBox=input_box:
                       handle_shift_send(inputBox))

    baseFrame.pack(fill='both')
    myscrollbar.pack(side='right', fill='y')
    canvas.pack(side='left', fill='both', expand=True)
    input_box.pack(side='left', anchor='w')
    button.pack(side='left', anchor='sw')

    # Give the input box focus
    input_box.focus()

    window.protocol("WM_DELETE_WINDOW", on_close)
    window.after(0, checkForMessages)


def handle_shift_send(input_box: tk.Text):
    """
    Used when sending a message using shift return. Waits 100ms
    before sending the message so that the return key is entered with
    the message rather than after it is sent. If it is done after then
    the cursor will be on line 2 when the user wants to type again.

    Paramters:
        input_box (tk.Text): Message box
    """
    input_box.after(100, handle_send, input_box)


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
        label = tk.Label(text='You:\n' + msg,
                         master=frame,
                         justify='left',
                         wraplength=LABEL_WIDTH,
                         relief='raised')
        label.pack(anchor='w')
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
