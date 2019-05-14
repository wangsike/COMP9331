
# COMP9331 Lab2
# server execute: java PingServer port
# client execute: python PingClient.py host port
# get serverName, serverPort from command line

from socket import *
import time
import sys

serverName = sys.argv[1]
serverPort = int(sys.argv[2])
clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.settimeout(1)


count = 0
RTT_list = [ ]
while count < 10:
	try:
		request_time = time.time()
		timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(request_time))
		message = 'PING ' + str(count) + ' ' + timestamp + ' \r\n'

		clientSocket.sendto(message, (serverName, serverPort))
		modifiedMessage, serverAddress = clientSocket.recvfrom(2048)
		response_time = time.time()
		time.sleep(1)

	except timeout:
		print ('ping to %s, seq = %d, time out' %(serverName, count))
		count += 1
		continue

	RTT = round(response_time - request_time, 3) * 1000
	RTT_list.append(RTT)
	modifiedMessage = modifiedMessage.decode()
	print ('ping to %s, seq = %d, rtt = %d ms' %(serverName, count, RTT))
	count += 1

min_rtt = min(RTT_list)
max_rtt = max(RTT_list)
ave_rtt = sum(RTT_list)/len(RTT_list)

print('The minimum RTT is %d ms.' % min_rtt)
print('The maximum RTT is %d ms.' % max_rtt)
print('The average RTT is %.2f ms.' % ave_rtt)

clientSocket.close()

