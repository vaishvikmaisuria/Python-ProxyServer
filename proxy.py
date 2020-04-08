import sys, os, time, socket, select

# Constants
PORT = 8888
WEB_PORT = 80
READ_AMNT = 4096
TIMEOUT = 600

def parse_header(data):
    """
    Parse the response from a web page.

    @param data: the data to parse
    @return: a list containing each line from the response, separated by the network newline
    """
    headers = data.split("\\r\\n")
    return headers

def URLtoFile(url):
    """
    Convert a URL to a format that can be saved as a file.

    @param url: the URL to convert
    @return: a valid filename
    """
    return url.replace("/", "-")

def injectHTML(data, content='fresh', attime=0):
    """
    Given a string of HTML code, inject the notification box.

    @param data: HTML code
    @param content: determines which message to display
    @param time: the time to display in the notification box
    @return: the binary string to send to the user
    """

    if content == 'fresh':
        toAdd = "<p style=\'z-index:9999; position:fixed; top:20px; left:20px; width:200px; height:100px; background-color:yellow; padding:10px; font-weight:bold;\'>FRESH VERSION AT: "+time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))+"</p>"
    else:
        toAdd = "<p style=\'z-index:9999; position:fixed; top:20px; left:20px; width:200px; height:100px; background-color:yellow; padding:10px; font-weight:bold;\'>CACHED VERSION AS OF: "+time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(attime))+"</p>"

    # Get the data and remove the b'
    response = data.decode(errors='ignore')

    # Find Content-Length field
    contentLengthLoc = response.find("Content-Length: ")

    # Update the Content-Length
    if contentLengthLoc != -1:
        headers = str(data).split("\\r\\n")
        i = 0

        while "Content-Length" not in headers[i]:
            i += 1

        newLength = int(headers[i].split(" ")[1]) + len(toAdd)
        response = response.replace(headers[i], "Content-Length: " + str(newLength))

    if "Content-Type: text/html" in response:
        # Find the <body> tag
        bodyLocation = response.find("<body")

        if bodyLocation == -1:
            return data

        while response[bodyLocation] != ">":
            bodyLocation += 1
        
        beforeBody = response[:bodyLocation+1]
        afterBody = response[bodyLocation+1:]

        return (beforeBody + toAdd + afterBody).encode()
    return data

def cache_website(filename, client, host, path):
    """
    Send a GET request to the requested web server and cache the response.

    @param filename: the name of the cached page
    @param client: the client connection
    @return: None
    """
    f = open(filename, "ab+")

    # Create the socket to the website
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, 80))

    # Send the GET request to the webpage
    request = "GET /"+path+" HTTP/1.1\r\nHost: " + host + "\r\nConnection: close\r\n\r\n"
    s.send(request.encode())

    # Receive the response from the web page and cache it. Then, send it to the user.
    while True:
        try:
            receivedData = s.recv(READ_AMNT)

            if len(receivedData) > 0:
                f.write(receivedData)
            else:
                break
        except socket.error:
            continue
    f.close()
    s.close()

    # Now send the file to the user
    f = open(filename, "rb")
    client.sendall(injectHTML(f.read(), content='fresh'))
    f.close()


def request_cache(filename, client):
    """
    Send the data from a given cache file to the client.

    @param filename: the file to retrieve
    @param client: the client connection
    @return: None
    """
    f = open(filename, "rb")
    client.sendall(injectHTML(f.read(), content='cached', attime=os.path.getmtime(filename)))
    f.close()

def handle_data(data, s):
    """
    Given data and a connection, check if the data is cached and send it to the
    user. If it is not cached, cache it. On success, return 0. On failure, -1.

    @param data: the data to send to the socket
    @param s: the connection
    @return: an integer
    """
    parsed_headers = parse_header(str(data))[0].split(" ")
    full_path = parsed_headers[1].split("/")
    host = full_path[1]
    path = "/".join(full_path[2:])

    # Skip the favicon
    if host == 'favicon.ico':
        return -1

    # Create cache folder if it doesn't exist
    if not os.path.exists("cache/"):
        os.makedirs("cache/")

    # Check if the path is saved in the cache
    fileLocation = "cache/" + URLtoFile(parsed_headers[1])

    if os.path.exists(fileLocation):
        # The webpage is saved in cache.
        if time.time() - os.path.getmtime(fileLocation) > CACHED_TIME:
            # This cached entry has expired.          
            os.remove(fileLocation)
            cache_website(fileLocation, s, host, path)
        else:
            request_cache(fileLocation, s)
    else:
        # The webpage is not saved in cache.
        cache_website(fileLocation, s, host, path)
    return 0

if __name__ == "__main__":

    # Set the cache timeout.
    if(len(sys.argv) == 2):
        CACHED_TIME = int(sys.argv[1])
    else:
        print("Usage: python3 proxy.py <cache timeout>")
        exit(-1)

    # Create the client socket.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', PORT))
    sock.setblocking(0)
    sock.listen(5)

    # Array for Select
    inputs = [sock]

    while len(inputs) > 0:
        read_s, write_s, exc_s = select.select(inputs, [], [], TIMEOUT)

        for s in read_s:
            if s == sock:
                # Accept new connection
                connection, client_addr = sock.accept()
                connection.setblocking(0)
                inputs.append(connection)
            else:
                try:
                    data = s.recv(READ_AMNT)

                    if data:
                        handle_data(data, s)
                    else:
                        inputs.remove(s)
                        s.close()
                except socket.error:
                    inputs.remove(s)
                    s.close()
    sock.close()
