#Step 3: Enable caching
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


def handle_cache(website_host, website_path, client):
    """
        Creates cache folder and stores cache if it does not exist, if it does exist it send the cache.

        Parameters:
            website_host (str): The string which is the host to the webpage.
            website_path (str): the string which is the path to the webpage.
            client (socket): The socket which is connect to the client so you can send back the webpage
        Returns:
            -1 (int): if the website host is a favicon
             0 (int): otherwise
    """
    # Skip the favicon
    if website_host == 'favicon.ico':
        return -1

    # Create cache folder
    if not os.path.exists("cache/"):
        os.makedirs("cache/")

    # check if the website folder exists 
    # if(len(website_path) > 0):      
    #     cacheLocation = "cache/" + website_host + (website_path.replace("/", ""))
    # else:
    #     cacheLocation = "cache/" + website_host

    cacheLocation = "cache/" + website_host + (website_path.replace("/", ""))

    # if the webpage is cached 
    if os.path.exists(cacheLocation):
        if ((time.time() - os.path.getmtime(cacheLocation)) > CASHE_TIMEOUT):
            os.remove(cacheLocation)
            cache_webpage(cacheLocation, website_host, website_path, client)
        else:
            get_cache(cacheLocation, client)
    else:
        # webpage is not cached then create cache
        cache_webpage(cacheLocation, website_host, website_path, client)    
    return 0

def get_cache(cacheLocation, client):
    """
        Get cached webpage data from file and sends it to the client. 

        Parameters:
            cacheLocation (str): The string which is the path to the cached folder containing the webpage.
            client (socket): The socket which is connect to the client so you can send back the webpage
    """
    f = open(cacheLocation, "rb")
    # finalOutput = injectNotification(f.read(), "cached", cacheLocation)
    # injectHTML(f.read(), content='cached', attime=os.path.getmtime(cacheLocation))
    
    client.sendall(injectNotification(f.read(), "cached", cacheLocation))
    f.close()

def cache_webpage(cacheLocation, website_host, website_path, client):
    """
        Create a socket connection to website server and send GET request and cache the response. 

        Parameters:
            cacheLocation (str): The string which is the path to the cached folder containing the webpage.
            website_host (str): The string which is the host to the webpage.
            website_path (str): the string which is the path to the webpage.
            client (socket): The socket which is connect to the client so you can send back the webpage.
    """
    # create the file to write the cache
    file = open(cacheLocation, "ab+")
    # Create an INET, STREAMing socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((website_host, WEB_PORT))
    # Send the GET request to the requested server add Accept-Encoding so you never get gzip format
    request = "GET /"+website_path+" HTTP/1.1\r\nHost: " + website_host +"\r\nAccept-Encoding: identity" + "\r\nConnection: close\r\n\r\n"
    s.send(request.encode())

    # Transfer the response from the web server, cache it, and then send it back to the user
    while True:
        try:
            webData = s.recv(DATA_LIMIT)
            if webData:
                print(webData)
                # write to the file
                file.write(webData)
            else:
                break
        except socket.error:
            continue
    file.close()
    s.close()

    # send the cache content back to the client
    f = open(cacheLocation, "rb")
    finalData = injectNotification(f.read(),'fresh', cacheLocation)
    client.sendall(finalData)
    # injectNotification(f.read(), "fresh", cacheLocation)
   
    f.close()

def injectNotification(cachedContent, type, fileName):
    """
        Given the Webpage content inject the  

        Parameters:
            cachedContent (str): The string which is the content of the webpage.
            type (str): The string which indicates whether the displayed web page is a fresh version or a cached version
            fileName (str): The string which is the path to the cached folder containing the webpage.
        Return:
            Result (str): The string to send back to the client socket
    """
    # Last time when the file was modified
    fileTime = os.path.getmtime(fileName) 

    if type == 'fresh':
        addHTML = "<p style='z-index:9999; position:fixed; top:20px; left:20px; width:200px; height:100px; background-color:yellow; padding:10px; font-weight:bold;'>FRESH VERSION AT: "+ time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())) +"</p>"
    else:
        addHTML = "<p style='z-index:9999; position:fixed; top:20px; left:20px; width:200px; height:100px; background-color:yellow; padding:10px; font-weight:bold;'>CACHED VERSION AS OF: "+ time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(fileTime)) +"</p>"
    

    # convert bytes to string and remove the b'
    dataHTML = cachedContent.decode(errors='ignore')

    # find the content length tag
    contentLength = dataHTML.find("Content-Length:")
    
    i = 0
    # check if the content length tag exist
    if contentLength != -1:
        dataHeaders = str(cachedContent).split("\\r\\n")
        while "Content-Length" not in dataHeaders[i]:
            i +=1
        # find the content length
        contentLength = int(dataHeaders[i].split(" ")[1])
        # update the length 
        finalLength = contentLength + len(addHTML)
        dataHTML = dataHTML.replace(dataHeaders[i], "Content-Length: " + str(finalLength))

    #find the <body> tag
    bodyTagloc = dataHTML.find("<body")
    
    # check if the body tag exists 
    if bodyTagloc == -1:
        return cachedContent

    #body tag has styles and stuff in it so find >
    while dataHTML[bodyTagloc] != ">":
        bodyTagloc +=1
    # inject the notification box to the web page
    final = dataHTML[:bodyTagloc+1] + addHTML + dataHTML[bodyTagloc+1:] 
    return final.encode()


if __name__ == "__main__":

    # check the arguments for cache timeout
    if len(sys.argv) == 2:
        CASHE_TIMEOUT = int(sys.argv[1])
    else:
        print("Error: Use python3 part4.py 120 (120 is the cashe timeout)")
        exit(-1)

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
                # output[connection] = []
            else:
                try:
                    print("Listening for new website")
                    data = s.recv(DATA_LIMIT)
                    if data:
                        # string parse the url out 
                        website_host, website_path = request_parser(data)
                        handle_cache(website_host, website_path, s)
                    else:
                        inputs.remove(s)
                        s.close()
                except socket.error:
                    inputs.remove(s)
                    s.close()
                
    clientsock.close()
