#socket_echo_server.py
import sys, os, time, socket, select
PORT = 8888
WEB_PORT = 80
DATA_LIMIT = 4096
TIMEOUT = 600

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



if __name__ == "__main__":

    # Create a TCP/IP socket (Browser Client)
    clientsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind the socket to the port
    server_address = ('localhost', PORT)
    print('starting up on {} port {}'.format(*server_address))
    clientsock.bind(server_address)
    # make the socket nonblocking.
    clientsock.setblocking(0)
    # Listen for 5 incoming connections
    clientsock.listen(5)
    # Input array for Select
    inputs = [clientsock]
    # Output array for Select
    output = {}

    while inputs:
        read_sock, write_sock, exceptional = select.select(inputs, [], [], TIMEOUT)

        for s in read_sock:
            if s == clientsock:
                # Accept new connection
                connection, client_address = clientsock.accept()
                connection.setblocking(0)
                inputs.append(connection)
                output[connection] = []
            else:
                try:
                    print('connection from', s)
                    print("Listeing for new website")
                    data = s.recv(DATA_LIMIT)
                    if data:
                        # string parse the url out 
                        website_host, website_path = request_parser(data)
                        #create an INET, STREAMing socket
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                        # Send the GET request to the requested server
                        request = "GET /"+website_path+" HTTP/1.1\r\nHost: " + website_host + "\r\nConnection: close\r\n\r\n"
                        s.connect((website_host, WEB_PORT))
                        s.send(request.encode())
                        # Transfer the response from the web server back to the user
                        while True:
                            try:
                                webData = s.recv(DATA_LIMIT)
                                if len(webData) > 0:
                                    print(webData)
                                    connection.sendall(webData)
                                else:
                                    print("no data")
                                    break
                            except socket.error:
                                continue
                    else:
                        inputs.remove(s)
                        s.close()
                except socket.error:
                    continue
                
    clientsock.close()
