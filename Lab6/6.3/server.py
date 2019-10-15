from rdt import socket_
server = socket_(syn=1)
server.bind(('127.0.0.1', 8080))
while True:
    data, addr = server.recvfrom()
    print('Receive: ' + str(data))

