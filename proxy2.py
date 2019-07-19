import socket
import http.client
import email
import io
import pprint
import time
import brotli
import zlib 
import threading
import select
import sys

debug = 1

def print_debug(msg):
    if debug:
        print msg

def connect_to_host(client):

    readable, writable, exceptional = select.select([client], [], [], 10)
    for c in readable:
        if c is client:
            data = client.recv(10000)
            if not data:
                print ": No Data available for reading/closed connection"
                return -1
    else:
        print "timeout occured"

    request_line, headers_alone = data.split("\r\n", 1)
        
    command = request_line.split()
    print_debug(command)
    
    if command[0] != "CONNECT" and command[0] != "POST":
        print "NO CONNECT OR POST COMMAND!"
        return -1

    server = socket.socket()

    if command[0] == "POST":
        address = command[1].split("/")
        print address
        print_debug("Opened connection with " + address[2] + "port " + "80")
        server.connect((address[2], 80))
        server.sendall(data)

    if command[0] == "CONNECT":
        address = command[1].split(":")
        print_debug("Opened connection with " + address[0] + "port " + address[1])
        server.connect((address[0], int(address[1])))
        response = "\r\n\r\n" + command[2] + " 200 OK\r\n\r\n"
        print_debug(response)
        client.sendall(response)
    

    print_debug("end")
    return server

MAX_BYTES=10000

def thread1(client, server):

    while True:
        try:

            readable, writable, exceptional = select.select([client, server], [], [])
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
        
        server = connect_to_host(client)
        if server == -1:
            print "connect_to_host() failed"
            client.close()
            continue

        threads = list()
        x = threading.Thread(target=thread1, args=(client, server))
        x.start()
        threads.append(x)
        #thread1(client, server)

        #server.close()
        #client.close()
        continue
