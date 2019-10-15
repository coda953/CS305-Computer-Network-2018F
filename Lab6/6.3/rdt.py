from udp import UDPsocket
from socket import *
import struct
import time
import threading


# 计算检验和
def calc_checksum(payload):
    sum = 0
    for byte in payload:
        sum += byte
    sum = -(sum % 256)
    return sum & 0xFF


# 验证信息的正确性
def calc_sum(payload):
    sum = 0
    for byte in payload:
        sum += byte
    return sum


# 将数字转为四字节的16进制字符串
def tran_into_hex_str_four(message):
    num = str(hex(message))
    le = 10 - len(num)
    re = '0' * le + num[2:]
    return re


# 打包十六进制字符串，转化为udp的16进制报文
def trans_into_hex(message):
    re = b''
    key = 0
    while key < len(message):
        intg = int(message[key:key+2], 16)
        re = re + struct.pack('B', intg)
        key = key + 2
    return re


# 数字转换
def ascii_to_num(message):
    key = 0
    re = 0
    num = len(message)
    while key < num:
        re = re + 256**(num-1-key)*int(message[key])
        key = key + 1
    return re


# 将文本转换为十六进制udp内容
def tran_into_hex_str(message, length):
    num = str(hex(message))
    le = length + 2 - len(num)
    re = '0' * le + num[2:]
    return re


# 数字转换
def two_byte_ascii_to_num(message):
    key = 0
    re = 0
    while key < len(message):
        re = re + 16**(3-key)*int(message[key:key+1])
        key = key + 1
    return re


# 将字符串payload转化为比特码payload
def payload_code_tran(message):
    key = 0
    re = b''
    while key < len(message):
        re = re + struct.pack('B', ord(message[key:key + 1]))
        key = key + 1
    return re


# 将信息封装为一个payload
class payload():
    def __init__(self, syn=0, fin=0, ack=0, seq=0, seq_ack=0, payload=''):
        self.syn = syn
        self.fin = fin
        self.ack = ack
        self.seq = seq
        self.seq_ack = seq_ack
        self.payload = payload
        self.len = len(payload)
        self.payload_code = payload_code_tran(payload)
        self.payload_list = [syn, fin, ack]
        self.decimal_to_one_byte_hex(self.seq, 8)
        self.decimal_to_one_byte_hex(self.seq_ack, 8)
        self.decimal_to_one_byte_hex(self.len, 8)
        key = 0
        while key < len(payload):
            self.payload_list.append(ord(payload[key]))
            key = key + 1
        self.checksum = calc_checksum(self.payload_list)

    # 字符串化
    def to_ascii(self):
        re = struct.pack('B', self.syn) + struct.pack('B', self.fin) + struct.pack('B', self.ack) + trans_into_hex(tran_into_hex_str(self.seq, 8))
        re = re + trans_into_hex(tran_into_hex_str(self.seq_ack, 8))
        re = re + trans_into_hex(tran_into_hex_str(self.len, 8))
        re = re + trans_into_hex(tran_into_hex_str(self.checksum, 4))
        re = re + self.payload_code
        return re

    # 十进制数字转化为特定长度的十六进制
    def decimal_to_one_byte_hex(self, num, len):
        str = hex(num)
        length = str.__len__()
        str = '0' * (len - (length - 2)) + str[2:]
        key = 0
        while key < str.__len__():
            self.payload_list.append(int(str[key:key + 2], 16))
            key += 2


# 解析收到的payload
class payload_resolver():
    def __init__(self, message):
        self.checksum_list = []
        self.syn = message[0]
        self.fin = message[1]
        self.ack = message[2]
        self.seq = ascii_to_num(message[3:7])
        self.seq_ack = ascii_to_num(message[7:11])
        self.len = ascii_to_num(message[11:15])
        self.checksum = ascii_to_num(message[15:17])
        self.payload = message[17:]
        if calc_checksum(message) == 0:
            self.jug = True
        else:
            self.jug = False

    # 字符串化
    def to_string(self):
        re = ''
        re = re + 'SYN: ' + str(self.syn) + '\n'
        re = re + 'FIN: ' + str(self.fin) + '\n'
        re = re + 'ACK: ' + str(self.ack) + '\n'
        re = re + 'SEQ: ' + str(self.seq) + '\n'
        re = re + 'SEQ_ACK: ' + str(self.seq_ack) + '\n'
        re = re + 'LEN: ' + str(self.len) + '\n'
        re = re + 'CHECKSUM: ' + str(self.checksum) + '\n'
        re = re + 'PAYLOAD: ' + str(self.payload) + '\n'
        re = re + 'JUG: ' + str(self.jug) + '\n'
        return re


# rdt传输udp
class socket_(UDPsocket):
    def __init__(self, window_size=3, base=1, next_sequence=1, recent_seq=0, retrans_time=2, syn=0):
        super().__init__()
        self.send_socket = socket(AF_INET, SOCK_DGRAM)
        self.seq = {}
        self.seq_ack = {}
        self.message = None
        self.window_size = window_size
        self.datas = []
        self.base = base
        self.next_sequence = next_sequence
        self.recent_seq = recent_seq
        self.send_process = threading.Thread(target=self.send_process)
        self.recv_process = threading.Thread(target=self.recv_process)
        self.send_process_jug = False
        self.recv_process_jug = False
        self.syn = syn

    # 接受完整的信息
    def recvfrom(self):
        while True:
            UDPsocket.setblocking(self, 5)
            result = UDPsocket.recvfrom(self, bufsize=4096)
            if result is None:
                continue
            else:
                try:
                    data = payload_resolver(result[0])
                except:
                    continue
                address = result[1]
                if data.jug:
                    if address not in self.seq.keys():
                        self.seq[address] = 0
                        self.seq_ack[address] = 0
                    if data.seq is not self.seq_ack[address]:
                        re = payload(seq_ack=self.seq_ack[address])
                        UDPsocket.sendto(self, re.to_ascii(), address)
                        continue
                    else:
                        self.seq_ack[address] = data.seq + data.len
                        re = payload(seq_ack=self.seq_ack[address])
                        UDPsocket.sendto(self, re.to_ascii(), address)
                        break
                else:
                    if address not in self.seq.keys():
                        self.seq[address] = 0
                        self.seq_ack[address] = 0
                    re = payload(seq_ack=self.seq_ack[address])
                    UDPsocket.sendto(self, re.to_ascii(), address)
                    continue
        # print('Inside function: '+str(data.payload))
        return data.payload, address

    def recv(self):
        return self.recvfrom()[0]

    def send(self, data):
        message = data[0]
        address = data[1]
        bytes = message.to_ascii()
        UDPsocket.sendto(self, bytes, address)

    # 发送信息
    def sendto(self, data, address):
        if address not in self.seq.keys():
            self.seq[address] = 0
            self.seq_ack[address] = 0
        load = payload(payload=data, seq=self.recent_seq, seq_ack=self.seq_ack[address])
        self.datas.append([load, address])
        self.recent_seq += load.len

    # 发送进程，用于发送流水线中的报文
    def send_process(self):
        while True:
            if self.datas.__len__() > 0:
                max = self.window_size if self.datas.__len__() > self.window_size else self.datas.__len__()
                for key in range(0, max):
                    data = self.datas[key]
                    self.send(data)
            time.sleep(0.5)

    # 启动进程
    def start_send_process(self):
        self.send_process.setDaemon(True)
        self.send_process.start()

    def start_recv_process(self):
        self.recv_process.setDaemon(True)
        self.recv_process.start()

    # 接受进程，用于接受发送出去的报文返回的ack，确认流水线中的报文正确的到达
    def recv_process(self):
        while True:
            UDPsocket.setblocking(self, 0)
            try:
                reply = UDPsocket.recvfrom(self, bufsize=4096)
                if reply is not None:
                    result = payload_resolver(reply[0])
                    if not result.jug:
                        continue
                else:
                    continue
            except:
                time.sleep(0.5)
                continue
            try:
                pack = self.datas[0]
                address = reply[1]
            except IndexError:
                continue
            if address not in self.seq.keys():
                self.seq[address] = 0
                self.seq_ack[address] = 0
            if result.seq_ack is self.seq[address] + pack[0].len:
                print('\"' + str(pack[0].payload) + '\"' + 'send successfully!')
                self.seq[address] += pack[0].len
                self.datas.remove(pack)
                continue
            elif result.seq is self.seq_ack[address] and result.syn is 1:
                print('\"' + str(result.payload) + '\"' + 'receive successfully!')
                self.seq_ack[address] += result.len
                continue
            else:
                time.sleep(0.5)
                continue
