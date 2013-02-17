import libbunny
import threading, getopt, sys, time

def usage():
	"""
	
	print out usage
	
	"""
	print "BunnyChat.py [COMANDS]"
	print "  -l              --   Listen mode, gets packets and prints data"
	print "  -s [data]       --   Send mode, sends packets over and over"
	print "  -m              --   Passive profiling of all the channels (1-11)"
	print "  -c [UserName]   --   Chat client mode"
	print "  -r              --   Reloop shows the mod/remainder of the specified channel"
	print "  -p              --   Ping/Pong testing, Run this on one machine and it will"
	print "                        respond with a pong."

def main():
	listen_mode = send_mode = scan_chans_mode = chat_mode = ping_mode = reloop_mode = False
	
	# parse arguments
	try:
		opts, args = getopt.getopt(sys.argv[1:],"hlrmpc:s:f:")
	except getopt.GetoptError as err:
		print str(err)
		usage()
		sys.exit(1)
	for opt, arg in opts:
		if opt == "-h":
			usage()
			sys.exit(0)
		elif opt == "-f":
			config_file = arg
		elif opt == "-l": 
			listen_mode = True
		elif opt == "-r":
			reloop_mode = True
		elif opt == "-s":
			send_mode = True
			send_data = arg
		elif opt == "-m":
			scan_chans_mode = True
		elif opt == "-c":
			UserName = arg
			chat_mode = True
		elif opt == "-p":
			ping_mode = True
			
	if listen_mode:
		print "Bunny in listen mode"
		print "Building model: . . . "
		bunny = libbunny.Bunny()
		print "Bunny model built and ready to listen"
		while True:
			try:
				print bunny.recvBunny()
			except libbunny.TimeoutWarning:
				pass
	elif reloop_mode:
		bunny = libbunny.Bunny()
		bunny.inandout.reloop()
		
	elif send_mode:
		if send_data is not None:
			bunny = libbunny.Bunny()
			print "Bunny model built"
			bunny.model.printTypes()
			bunny.model.printMacs()
			print "sending message: %s" % send_data
			bunny.sendBunny(send_data)
			
			while True:
				print "again? [Y/N]"
				input = sys.stdin.readline()
				if input == "Y\n" or input == "y\n":
					print "sending message: %s" % send_data
					bunny.sendBunny(send_data)
				elif input == "N\n" or input == "n\n":
					sys.exit()
		else:
			print usage()
			sys.exit()
			
	elif chat_mode:
		print "chat client mode:"
		print "building traffic model: . . "
		bunny = libbunny.Bunny()
		
		print "built traffic model"
		bunny.model.printTypes()
		bunny.model.printMacs()
		print "starting threads: "
		
		# create list of threads
		# one thread for input and the other for output.
		# both use stdin or stdout
		workers = [StdInThread(bunny, UserName), BunnyThread(bunny, UserName)]
		
		for worker in workers:
			worker.setDaemon(True)
			worker.start()
		
		# loop through every 3 seconds and check for dead threads
		while True:
			for worker in workers:
				if not worker.isAlive():
					sys.exit()
			time.sleep(3)
		
	elif scan_chans_mode:
		for c in range(1,12):
			chan = c
			print "\nChannel: %d" % chan			
			bunny = libbunny.Bunny()
			bunny.model.printTypes()
			#bunny.model.printMacs()
	elif ping_mode:
		bunny = libbunny.Bunny()
		print "Model completed, ready to play pong"
		while True:
			try:
				text = bunny.recvBunny()
				#print text.rstrip("\xff")
				if text.find("ping") != -1:
					bunny.sendBunny("CNC:pong\xff")
					print "Pong sent"
				
			except libbunny.TimeoutWarning:
				pass
		
	else:
		usage()
		sys.exit()

# quick and dirty threading for the send/rec chat client mode.
class StdInThread(threading.Thread):
	"""
	
	Thread class for reading from STDIN
	
	"""
	# takes the bunny object as an argument
	def __init__(self, bunny, username):
		self.bunny = bunny
		self.username = username
		threading.Thread.__init__(self)
	def run (self):
		print "ready to read! (type: /quit to kill)"
		while True:
			input = sys.stdin.readline().strip("\n")
			if input == "/quit":
				break
			# send with UserName and a trailer to prevent the stripping of 'A's as padding
			# see the comment in the __init__() in AEScrypt
			self.bunny.sendBunny(self.username + ": " + input + "\xff")
			
class BunnyThread(threading.Thread):
	"""
	
	Thread class for reading from the bunny interface
	
	"""
	# takes the bunny object as an argument
	def __init__(self, bunny, username):
		self.bunny = bunny
		self.username = username
		threading.Thread.__init__(self)
	def run (self):
		# Standard calling should look like this:
		while 1:
			try:
				text = self.bunny.recvBunny()
			except libbunny.TimeoutWarning:
				continue
			# if we get our own UserName do not display it,
			# FIX THIS
			if text.split(":")[0] == self.username:
				continue
			else:
				# strip out the ending char.
				print text.rstrip("\xff")
				
		
if __name__ == "__main__":
	main()