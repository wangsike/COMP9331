
# COMP9331 Lab3
# (1) Create a connection socket when contacted by a client (browser).
# (2) Receive HTTP request from this connection. Your server should only process GET request. 
#     You may assume that only GET requests will be received.
# (3) Parse the request to determine the specific file being requested. 
# (4) Get the requested file from the server's file system.
# (5) Create an HTTP response message consisting of the requested file preceded by header lines. 
# (6) Send the response over the TCP connection to the requesting browser.
# (7) If the requested file is not present on the server, 
#     the server should send an HTTP "404 Not Found" message back to the client.
# (8) The server should listen in a loop, waiting for next request from the browser.

from socket import *
import sys

serverPort = int(sys.argv[1])                               # get serverPort from command line
serverSocket = socket(AF_INET, SOCK_STREAM)					# (1)
serverSocket.bind(('127.0.0.1', serverPort))				
serverSocket.listen(1)

print('The server is ready to receive\n')				

# (8)
while True:

	print "Ready to serve..."
	connectionSocket, addr = serverSocket.accept()

	try:
		request = connectionSocket.recv(1024)				# (2) receives get request from client
		message = request.split()[1]						# (3) parse get request
		FileName = message.replace('/', '')

		print(FileName + '\n')						
		f = open(FileName)									# (4)
		httpoutput = f.read()

		connectionSocket.send('HTTP/1.1 200 OK\n\n')		# (5)
		connectionSocket.send(httpoutput)					# (6)
		connectionSocket.close()

	except IOError:
		connectionSocket.send('HTTP/1.1 404 Not Found\n\n') 
		connectionSocket.send('<h1><center>404 Not Found</center></h1>')	# (7)
        connectionSocket.close()




