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

debug = 0
error = 1

def print_debug(msg):
    if debug:
        print msg

def print_error(msg):
    if error:
        print msg

def connect_to_host(client):
    data = ""
    try:
        readable, writable, exceptional = select.select([client], [], [], 5)
        if not readable and not writable and not exceptional:
            print_error(": Select timeout occured")
            return -1

        for c in readable:
            if c is client:
                data = client.recv(10000)
                if not data:
                    print_error(": no data available for reading/closed connection")
                    return -1

    except socket.error:
        print_error(": Socket error occured")
        return -1
    except socket.timeout:
        print_error(": Socket timeout occured")
        return -1
 
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
            msg = "<html><body> <h2> The host " + address[2] + " not found. </h2> </body></html>"
            response = "\r\n\r\n" + command[2] + " 400\r\nContent-length: " + str(len(msg)) + "\r\n\r\n" + msg
            print_debug(response)
            client.sendall(response)
            server.close()
            return -1

        response = "\r\n\r\n" + "HTTP/2.0" + " 200\r\n\r\n"
        print_debug(response)
        client.sendall(response)

    return server

MAX_BYTES=10000

def proxy_thread(client):

    server = connect_to_host(client)
    if server == -1:
        print_error(": connect_to_host() failed")
        client.close()
        return

    while True:
        try:

            readable, writable, exceptional = select.select([client, server], [], [], 5)
            if not readable and not writable and not exceptional:
                print_error(": Select timeout in main loop")
                server.close()
                client.close()
                return

            for s in readable:
                if s is server:
                    data = server.recv(MAX_BYTES)
                    #print_debug("server:" + data[0:10])
                    client.sendall(data)
                if s is client:
                    data = client.recv(MAX_BYTES)
                    #print_debug("client:" +data[0:10])
                    server.sendall(data)

        except socket.error:
            print_error(": Socket error occured")
            server.close()
            client.close()
            return

if __name__ == "__main__":

    sock = socket.socket()
    sock.bind(("", 8080))
    sock.listen(1)

    while True:
        client, addr = sock.accept()
 
        threads = list()
        x = threading.Thread(target=proxy_thread, args=(client,))
        x.start()
        threads.append(x)
