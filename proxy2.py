import socket
import httplib
import email
import io
import pprint
import time
import zlib 
import threading
import select
import sys
import signal

debug = 0
error = 1


def print_debug(msg):
    if debug:
        print msg

def print_error(msg):
    if error:
        print msg

MAX_BYTES=10000

def connect_to_host(client):
    try:
        data = client.recv(MAX_BYTES)
    except socket.error:
        print_error(": Socket.recv() exception")
        retutn -1
 
    if not data:
        print_error(": Received empty buffer. Exiting...")
        return -1

    try:
        request_line, headers_alone = data.split("\r\n", 1)
    except:
        print_error(": Can't split the request line: " + data)
        return -1

    command = request_line.split()
    print_debug(command)
 
    if command[0] != "CONNECT" and command[0] != "POST" and command[0] != "GET":
        print_error(": Wrong command in Http request (not CONNECT/POST/GET): " + command[0])
        return -1

    server = socket.socket()

    if command[0] == "POST" or command[0] == "GET":
        address = command[1].split("/")
        print_debug(address)
        print_debug("Opened connection with " + address[2] + " port " + "80")
        try:
            server.connect((address[2], 80))
        except:
            msg = "<html><body> <h2> The host " + address[2] + " not found. </h2> </body></html>"
            response = "\r\n\r\n" + command[2] + " 400\r\nContent-length: " + str(len(msg)) + "\r\n\r\n" + msg
            print_debug(response)
            client.sendall(response)
            server.close()
            return -1

        server.sendall(data)

    if command[0] == "CONNECT":
        address = command[1].split(":")
        print_debug("Opened connection with " + address[0] + " port " + address[1])
        try:
            server.connect((address[0], int(address[1])))
        except:
            msg = "<html><body> <h2> The host " + address[0] + " not found. </h2> </body></html>"
            response = "\r\n\r\n" + command[2] + " 400\r\nContent-length: " + str(len(msg)) + "\r\n\r\n" + msg
            print_debug(response)
            client.sendall(response)
            server.close()
            return -1

        response = "\r\n\r\n" + "HTTP/2.0" + " 200\r\n\r\n"
        print_debug(response)
        client.sendall(response)

    return server

def handler_thread(q):

    while True:
        data, evt = q.get(1)
        evt.set()
        q.task_done()

        if str(data) == "exit":
            return

        client = int(data)

    return

exit_flag = 0

def signal_handler(signal, frame):

    global exit_flag
    exit_flag = 1

    if debug:
        import pdb
        pdb.set_trace()

if __name__ == "__main__":

    signal.signal(signal.SIGINT, signal_handler)

    sock = socket.socket()
    sock.bind(("", 8080))
    sock.listen(1)

    epoll = select.epoll()
    epoll.register(sock.fileno(), select.POLLIN)

    connections = {}

    connections[sock.fileno()] = sock

    while True:
        if exit_flag:
            for item in list(connections):
                s = connections[item]
                del connections[item]
                epoll.unregister(s.fileno())
                s.close()

            epoll.close()
            sock.close()
            print_error("Server has been closed. Exiting...")
            sys.exit()

        try:
            events = epoll.poll()
            for fileno, event in events:
                if fileno == sock.fileno():
                    try:
                        client, addr = sock.accept()
                        client.setblocking(0)
                        epoll.register(client.fileno(), select.EPOLLIN | select.EPOLLHUP)
                        connections[client.fileno()] = client

                    except socket.error:
                        print_error(": socket.accept() failed.")
                        pass

                elif event & select.POLLIN:
                    try:
                        client = connections[fileno]
                    except:
                        print  "fileno " + str(fileno)
                        epoll.unregister(fileno)
                        continue

                    if fileno == client.fileno():
                        server = connect_to_host(client)
                        if server == -1:
                            print_error(": connect_to_host() failed")
                            epoll.unregister(client.fileno())
                            connections[client.fileno()] = 0
                            del connections[client.fileno()]
                            client.close()
                            continue

                        server.setblocking(0)

                        epoll.register(server.fileno(), select.EPOLLIN | select.EPOLLHUP)

                        connections[client.fileno()] = server
                        connections[server.fileno()] = client
                        continue

                    server = connections[client.fileno()]

                    if fileno != server.fileno():
                        print_error("Sockets data are not equal: " + str(fileno) + " = " + str(server.fileno()))
                        continue
 
                    try:
                        data = server.recv(MAX_BYTES)
                        if not data:
                            epoll.unregister(client.fileno())
                            epoll.unregister(server.fileno())
                            connections[client.fileno()] = 0
                            connections[server.fileno()] = 0
                            del connections[client.fileno()]
                            del connections[server.fileno()]
                            client.close()
                            server.close()
                            continue
                        client.sendall(data)
                    except socket.error:
                        epoll.unregister(client.fileno())
                        epoll.unregister(server.fileno())
                        connections[client.fileno()] = 0
                        connections[server.fileno()] = 0
                        del connections[client.fileno()]
                        del connections[server.fileno()]
                        client.close()
                        server.close()
                        pass

                elif event & select.POLLHUP:
                    try:
                        print_debug("select.POLLHUP")
                        client = connections[fileno]
                        server = connections[client.fileno()]

                        if fileno != server.fileno():
                            print_error("i :Sockets data are not equal: " + str(fileno) + " = " + str(server.fileno()))
                            continue

                        epoll.unregister(client.fileno())
                        epoll.unregister(server.fileno())
                        connections[client.fileno()] = 0
                        connections[server.fileno()] = 0
                        del connections[client.fileno()]
                        del connections[server.fileno()]
                        client.close()
                        server.close()
                    except socket.error:
                        print_error(": socket.close() failed")
                        pass
        except:
            for item in list(connections):
                s = connections[item]
                del connections[item]
                epoll.unregister(s.fileno())
                s.close()

            epoll.close()
            sock.close()
            print_error("Server has been closed. Exiting...")
            sys.exit()
