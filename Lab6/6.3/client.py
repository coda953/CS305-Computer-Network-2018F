from rdt import socket_
client = socket_()
# 创建守护进程，实现流水线传输(不用等上一条信息发送完再发送下一条信息)
client.start_send_process()
client.start_recv_process()
while True:
    # 非阻塞
    DATA = (input(''))
    client.sendto(DATA, ('127.0.0.1', 8080))
