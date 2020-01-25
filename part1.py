#socket_echo_server.py
import sys, os, time, socket, select

PORT = 8880
WEB_PORT = 80
DATA_LIMIT = 4096

def request_parser(data):
    """
        Returns the host and path for a valid HTTP request. 

        Parameters:
            data (str): The string which is the request to be parsed.
        
        Returns:
            get_host(str1):The string which represents the host of the HTTP request.
            get_path(str1):The string which represetns the path of the HTTP request.
        
    """
    headers = str(data).split("\\r\\n")
    parsed_headers = headers[0].split(" ")
    website_url = parsed_headers[1].split("/")
    host = website_url[1]
    path = "/".join(website_url[2:])
    
    return (host, path)



# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ('localhost', PORT)
print('starting up on {} port {}'.format(*server_address))
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)

while True:
    # Wait for a connection
    print('waiting for a connection')
    connection, client_address = sock.accept()
    try:
        print('connection from', client_address)

        # Receive the data in small chunks and retransmit it
        while True:
            print("Listeing for new website")
            data = connection.recv(DATA_LIMIT)
            print('received {!r}'.format(data))
            # string parse the url out 
            website_host, website_path = request_parser(data)
           
            #create an INET, STREAMing socket
            websocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

             # Send the GET request to the requested server
            request = "GET /"+website_path+" HTTP/1.1\r\nHost: " + website_host + "\r\n\r\n"
            websocket.connect((website_host, WEB_PORT))
            websocket.send(request.encode())
            # Transfer the response from the web server back to the user
            while True:
                receivedData = websocket.recv(DATA_LIMIT)
                if len(receivedData) > 0:
                    print(receivedData)
                    connection.sendall(receivedData)
                else:
                    print("no data")
                    break
    finally:
        print("Closing connection")
        # Clean up the connection
        connection.close()