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

debug = 1

def print_debug(msg):
    if debug:
        print msg

def connect_to_host(client):
    data = ""
    try:
        readable, writable, exceptional = select.select([client], [], [], 5)
        if not readable and not writable and not exceptional:
            print "timeout occured"
            return -1

        for c in readable:
            if c is client:
                data = client.recv(10000)
                if not data:
                    print ": No Data available for reading/closed connection"
                    return -1

    except socket.error:
        print "Socket error"
        return -1
    except scoket.timeout:
        print "socket timeout"
        return -1
 
    if not data:
        print "how come?"

    try:
        request_line, headers_alone = data.split("\r\n", 1)
    except:
        print "->> Can't slpit the requst line"
        print data
        return -1

    command = request_line.split()
    print_debug(command)
 
    if command[0] != "CONNECT" and command[0] != "POST" and command[0] != "GET":
        print "NO CONNECT OR POST OR GET COMMAND!"
        return -1

    server = socket.socket()

    if command[0] == "POST" or command[0] == "GET":
        address = command[1].split("/")
        print address
        print_debug("Opened connection with " + address[2] + " port " + "80")
        try:
            server.connect((address[2], 80))
        except:
            response = "\r\n\r\n" + command[2] + " 400 Bad Request\r\n\r\n"
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
            response = "\r\n\r\n" + command[2] + " 400 Bad Request\r\n\r\n"
            print_debug(response)
            client.sendall(response)
            server.close()
            return -1

        response = "\r\n\r\n" + command[2] + " 200 OK\r\n\r\n"
        print_debug(response)
        client.sendall(response)

    print_debug("end")
    return server

MAX_BYTES=10000

def thread1(client):

    server = connect_to_host(client)
    if server == -1:
        print "connect_to_host() failed"
        client.close()
        return

    while True:
        try:

            readable, writable, exceptional = select.select([client, server], [], [], 5)
            if not readable and not writable and not exceptional:
                print "Timeout in loop!"
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

                continue;
        except socket.error, e:
            print e.args[0]
            print "closed channel"
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
        x = threading.Thread(target=thread1, args=(client,))
        x.start()
        threads.append(x)
        #thread1(client, server)

        #server.close()
        #client.close()
        continue
