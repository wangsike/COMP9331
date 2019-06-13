
# Student Number: z5148637

from socket import *
import sys
import time
import random
import pickle
import threading

ipaddress = "localhost"
BUFF = 2048
NUM = 50000

# Data structure for DHT packet
class DHT_packet():
	def __init__(self, Sequence, Acknowledgement, ACK, PING, FILE, QUIT, Data):
		self.Sequence = Sequence
		self.Acknowledgement = Acknowledgement
		self.ACK = ACK
		self.PING = PING
		self.FILE = FILE
		self.QUIT = QUIT
		self.Data = Data
		self.sourcePeer = int(sys.argv[1])

class DHT_peer():
	def __init__(self, peerID, successor1, successor2, MSS, drop_rate):

		self.peerID = peerID
		self.successor1 = successor1
		self.successor2 = successor2
		self.MSS = MSS
		self.drop_rate = drop_rate

		self.myPort = self.peerID + NUM
		self.successor1Port = self.successor1 + NUM
		self.successor2Port = self.successor2 + NUM
		self.predecessor1 = None
		self.predecessor2 = None
		self.lock = threading.Lock()

		self.file_ack = False

		# UDP init
		self.sendSocket = socket(AF_INET, SOCK_DGRAM) # IPV4 & UDP
		self.receiveSocket = socket(AF_INET, SOCK_DGRAM)
		self.receiveSocket.bind(("", self.myPort))
		self.receiveSocket.settimeout(11)

		# UDP receive thread
		UDP_thread = threading.Thread(target = self.UDP_receive)
		UDP_thread.setDaemon(True) # set the Dmaemon thread
		UDP_thread.start()

		# TCP receive thread
		TCP_thread = threading.Thread(target = self.TCP_receive)
		TCP_thread.setDaemon(True)
		TCP_thread.start()

		# Ping thread (UDP)
		Ping_thread = threading.Thread(target = self.Ping)
		Ping_thread.setDaemon(True)
		Ping_thread.start()

		# main thread
		self.main()
		

	# create an object which is packet
	def pack_Data(self, Sequence, Acknowledgement, ACK, PING, FILE, QUIT, Data):
		packet = DHT_packet(Sequence, Acknowledgement, ACK, PING, FILE, QUIT, Data)
		packet1 = pickle.dumps(packet)
		return packet1

	def unpack_Data(self, packet):
		return pickle.loads(packet)

	# Step 2: Ping(UDP)
	def Ping(self):
		while True:
			pingmessage1 = "A ping request message was received from Peer " + str(peerID) + "."
			list1 = [1, pingmessage1]
			list2 = [2, pingmessage1]
			packet1 = self.pack_Data(0, 0, 0, 1, 0, 0, list1)  # PING flag is 1
			packet2 = self.pack_Data(0, 0, 0, 1, 0, 0, list2)
			self.sendSocket.sendto(packet1, (ipaddress, self.successor1Port))  # UDP send
			self.sendSocket.sendto(packet2, (ipaddress, self.successor2Port))
			time.sleep(10)

	def UDP_receive(self):
		flag = 0
		while True:
			try:
				message, senderAddress = self.receiveSocket.recvfrom(BUFF)
				message = self.unpack_Data(message)
				# Receive Ping Request
				if (message.PING == 1): 
					print(message.Data[1])
					# Ping response
					pingmessage  = "A ping response message was received from Peer " + str(self.peerID) + "." 
					packet = self.pack_Data(0, 0, 1, 0, 0, 0, pingmessage)
					self.sendSocket.sendto(packet, (ipaddress, message.sourcePeer+NUM))

					# update predecessor
					if message.Data[0] == 1:
						self.predecessor1 = message.sourcePeer
					elif message.Data[0] == 2:
						self.predecessor2 = message.sourcePeer

				elif (message.ACK == 1):
					if (message.Data):
						print(message.Data)
					self.file_ack = True

				elif (message.FILE == 1):
					# receive file and save it(UDP)
					packet = self.pack_Data(0, 0, 1, 0, 0, 0, None)
					self.sendSocket.sendto(packet, (ipaddress, message.sourcePeer+NUM))
					if flag == 0:
						print(f"Received a response message from peer {message.sourcePeer}, which has the file {message.Data[0]}.")
						print("We now start receiving the file .........")
						f = open("received_file", "ab")
						f.write(message.Data[1])
						flag = 1
						if len(message.Data[1]) < self.MSS:
							f.close()
							print("The file is received.")
					else:
						f.write(message.Data[1])
						if len(message.Data[1]) < self.MSS:
							f.close()
							print("The file is received.")
					
			except Exception:
				# kill_Thread, update successors
				break

	def TCP_receive(self):
		Init_socket = socket(AF_INET, SOCK_STREAM)  # IPV4 & TCP
		Init_socket.bind((ipaddress, self.myPort))
		Init_socket.listen()
		while True:
			Connection_socket, addr = Init_socket.accept()
			data = Connection_socket.recv(BUFF)
			message = self.unpack_Data(data)
			try:
				# file request from other peer
				if message.FILE == 1:
					# message.data is filename
					filenum = message.Data
					filename = str(message.Data) + ".pdf"
					filehash = int(filenum%256)

					# 与下面的if else里的TCP_socket结合使用
					TCP_socket = socket(AF_INET, SOCK_STREAM)
					# evaluate if it is held at my location
					if self.peerID == filehash:
						print(f"File {filenum} is here.")
						print(f'A response message, destined for peer {message.sourcePeer}, has been sent.')
						self.send_File(filename, message.sourcePeer)

					elif (self.predecessor1 < filehash < self.peerID):
						print(f"File {filenum} is here.")
						print(f'A response message, destined for peer {message.sourcePeer}, has been sent.')
						self.send_File(filename, message.sourcePeer)

					elif (self.predecessor1 > self.peerID and self.predecessor1 < filehash):
						print(f"File {filenum} is here.")
						print(f'A response message, destined for peer {message.sourcePeer}, has been sent.')
						self.send_File(filename, message.sourcePeer)

					else: 
						# forward the message to next peer
						print(f'File {filenum} is not stored here.')
						print('File request message has been forwarded to my successor.')
						TCP_socket.connect((ipaddress, self.successor1Port)) # connect to successor1Port
						TCP_socket.send(data)
					TCP_socket.close()

				# quit message received (update successors)
				elif message.QUIT == 1:
					# message.Data is list1
					if message.Data[3] == 1:
						print(message.Data[0])
						self.successor1 = message.Data[1]
						self.successor2 = message.Data[2]

					elif message.Data[3] == 2:
						print(message.Data[0])
						#self.successor1 = message.Data[1]
						self.successor2 = message.Data[2]

					self.successor1Port = self.successor1 + NUM
					self.successor2Port = self.successor2 + NUM
					if self.successor1 and self.successor2:
						print(f'My first successor is now peer {self.successor1}.')
						print(f'My second successor is now peer {self.successor2}.')

			except ConnectionRefusedError:
				pass
			Connection_socket.close()


	# Step 3: Requesting a file (TCP)
	def request_File(self, filename):
		# if predecessors are None, they need to wait update
		if not (self.predecessor1 and self.predecessor2):
			pass
		try:
			print(f'File request message for {filename} has been sent to my successor.')
			packet = self.pack_Data(0, 0, 0, 0, 1, 0, int(filename)) # FILE flag is 1
			TCP_socket = socket(AF_INET, SOCK_STREAM)
			TCP_socket.connect((ipaddress, self.successor1Port))
			TCP_socket.send(packet)
			TCP_socket.close()
		except ConnectionRefusedError:
			pass

	# open file function
	def open_File(self, filename):
		f1 = open(filename, "rb")
		return f1

	# send file (UDP) 
	def send_File(self, filename, peer):
		self.sendSocket.settimeout(1)
		print("We now start sending the file .........")
		f = self.open_File(filename)
		while True:
			self.file_ack = False
			raw_data = f.read(int(self.MSS))
			if (str(raw_data) == "b''"):
				break
			list1 = [filename, raw_data]
			packet = self.pack_Data(0, 0, 0, 0, 1, 0, list1)
			randnum = random.random()
			if ( randnum >= self.drop_rate):
				self.sendSocket.sendto(packet, (ipaddress, peer+NUM))
			time.sleep(0.1)
			if (self.file_ack == False):
				self.sendSocket.sendto(packet, (ipaddress, peer+NUM))
				
			#message, senderAddress = self.receiveSocket.recvfrom(BUFF)
		f.close()
		print("The file is sent.")

	# name: responding_log.txt and requesting_log.txt
	def write_Log(self, logfile, event, time, seqnum, data_length, acknum):
		self.lock.acquire()
		logcontent = event.ljust(20) + str(round(currenttime - starttime), 2).ljust(11) 
		+ str(seqnum).ljust(11) + str(data_length).ljust(11) + str(acknum).ljust(11)
		with open(logfile, 'a') as f:
			f.write(logcontent)
		self.lock.release()

	# Step 4: Peer departure(TCP)
	def quit_Thread(self):
		if self.predecessor1 == None:
			# wait 11 seconds to check if predecessor1s just haven't been updated
			time.sleep(11)          
		try:
			# 把离开节点的 successor1和 successor2 等信息发送给离开节点的 predcessors
			string1 = "Peer " + str(self.peerID) + " will depart from the network."
			list1 = [string1, self.successor1, self.successor2, 1]
			list2 = [string1, self.peerID, self.successor1, 2]
			packet1 = self.pack_Data(0, 0, 0, 0, 0, 1, list1)  # QUIT flag is 1
			packet2 = self.pack_Data(0, 0, 0, 0, 0, 1, list2) 

			TCP_socket1 = socket(AF_INET, SOCK_STREAM)
			TCP_socket1.connect((ipaddress, self.predecessor1+NUM))
			TCP_socket1.send(packet1)  # send list data to predecessor
			TCP_socket1.close()

			TCP_socket2 = socket(AF_INET, SOCK_STREAM)
			TCP_socket2.connect((ipaddress, self.predecessor2+NUM))
			TCP_socket2.send(packet2)
			TCP_socket2.close()
			sys.exit(0)

		except (TypeError, ConnectionRefusedError):
			sys.exit(0)

	# Step 5: Kill peer(TCP)
	def kill_Thread(self):
			pass

	# Main
	def main(self):
		while True:
			command = input("")
			command.strip()

			if command == 'quit':
				self.quit_Thread()
			elif command[0:7] == 'request':
				try:
					filename = int(command[8:])
					if not (0 <= filename <= 9999):
						raise ValueError
					self.request_File(filename)
				except ValueError:
					pass
			else:
				pass


if __name__ == "__main__":
	peerID = int(sys.argv[1])
	successor1 = int(sys.argv[2])
	successor2 = int(sys.argv[3])
	MSS = int(sys.argv[4])
	drop_rate = float(sys.argv[5])
	peer = DHT_peer(peerID, successor1, successor2, MSS, drop_rate)


