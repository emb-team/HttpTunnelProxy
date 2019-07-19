import socket
import http.client
import email
import io
import pprint
import time
import brotli
import zlib 

if __name__ == "__main__":

    sock = socket.socket()
    sock.bind(("", 8080))
    sock.listen(1)

    while True:
        conn, addr = sock.accept()

        conn2 = 0
        data2 = ""
        first = 0
        sock2 = 0

        d = conn.recv(1024)
        #try: 
        #    data = zlib.decompress(data2, 16+zlib.MAX_WBITS)
        #except zlib.error:
        data = d
         
        if data:
            request_line, headers_alone = data.split("\r\n", 1)
            if conn2 == 0:
                print "openning connection with investing"
                n = request_line.split()
                for i in n:
                    print i
                print len(n)
                m = n[1].split(":")
                print m[0], m[1]
                if n[0] != "CONNECT":
                    print "not a Connect request"

                conn2 = http.client.HTTPSConnection(m[0], m[1])
        
            if conn2 == 0:
                print "fail to connect with investing"
                break;
            
            #message = email.message_from_string(headers_alone)
           # headers = dict(message.items())
           # del headers["Proxy-Connection"]
           # pprint.pprint(headers,width=160)

            headers = { 
                "Host": "www.investing.com",
                "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.5",
                "Connection": "keep-alive"
            }

            conn2.request("GET", "/", None, headers) 
            resp = conn2.getresponse()
            print (resp.status, resp.reason, resp.version)
            data2 = resp.read()
                #sock2 = resp.fileno()
                #sock2 = conn2.sock
            #else :
             #   sock2.sendall(data)
              #  data = sock2.recv(12000)

            #print data2
            #d=brotli.decompress(data2)
            d = zlib.decompress(data2, 16+zlib.MAX_WBITS)
            f = open("n.html", "w+")
            f.write(d)
            f.close()
           
            r = n[2] + " 200 OK\r\nDate: " + time.ctime() +"\r\nServer: Apache/2.2.14(Linux)\r\nContent-Length: " + str(len(data2)) +"\r\nContent-Type: text/html\r\nConnection: keep-alive\r\n"
            print r
            conn.sendall(r)
            conn.sendall(data2)

            conn.close()
