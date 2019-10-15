from socket import *
import datetime
import struct
# 解码时用于把16进制转为数字的词典
num_dict = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'a': 10, 'b': 11,
                'c': 12, 'd': 13, 'e': 14,
                'f': 15}
# 报文请求类型的映射
type_dic = {1: 'A', 2: 'NS', 5: 'CNAME', 15: 'MX', 16: 'TXT', 28: 'AAAA', 6: 'SOA'}


# 将一字节的16进制字符串转为数字
def str_hex_to_bin(st):
    return 16 * num_dict[st[0]] + num_dict[st[1]]


# 将二字节的16进制字符串转为数字
def str_four_hex_to_bin(st):
    return 16 * 16 * 16 * num_dict[st[0]] + 16 * 16 * num_dict[st[1]] \
           + 16 * num_dict[st[2]] + num_dict[st[3]]


# 将四字节的16进制字符串转为数字
def str_four_bytes_hex_to_bin(st):
    num = 0
    re = 0
    while num < 8:
        re = re + 16 ** (7 - num) * num_dict[st[num]]
        num = num + 1
    return re


# 将数字转为二字节的16进制字符串
def tran_into_hex_str(message):
    num = str(hex(message))
    le = 6 - len(num)
    re = '0' * le + num[2:]
    return re


# 将数字转为一字节的16进制字符串
def tran_into_hex_str_two(message):
    num = str(hex(message))
    le = 4 - len(num)
    re = '0' * le + num[2:]
    return re


# 将数字转为四字节的16进制字符串
def tran_into_hex_str_four(message):
    num = str(hex(message))
    le = 10 - len(num)
    re = '0' * le + num[2:]
    return re


# 解码16位udp报文，start位开始字节，end为结束字节
def message_resolver(message, start, end):
    re = ''
    while start < end:
        st = str(message[start:start + 1])[2:-1]
        if len(st) == 1:
            re = re + str(hex(ord(st)))[2:]
        else:
            re = re + st[2:]
        start = start + 1
    return re


# 解码16位udp报文，从第start字节开始往后解码
def message_resolver_to_end(message, start):
    re = ''
    while start < len(message):
        st = str(message[start:start + 1])[2:-1]
        if len(st) == 1:
            re = re + str(hex(ord(st)))[2:]
        else:
            re = re + st[2:]
        start = start + 1
    return re


# 解码16位udp报文，转化为正常的url地址
def get_query_name(message):
    re = ''
    start = 12
    num = 0
    while True:
        start = start + num
        st = str(message[start:start + 1])[2:-1]
        if len(st) == 1:
            num = ord(st)
        else:
            num = str_hex_to_bin(st[2:])
        if num == 0:
            break
        else:
            start = start + 1
            key = 0
            start_ = start
            while key < num:
                st = str(message[start_:start_ + 1])[2:-1]
                re = re + st
                start_ = start_ + 1
                key = key + 1
            re = re + '.'
    return re[:-1], start + 1


# 将RRs字符串化
def list_to_str(list):
    re = ''
    for a in list:
        re = re + '\n' + 'offset:' + a.offset
        re = re + '\n' + 'type:' + str(a.type)
        re = re + '\n' + 'cls:' + a.cls
        re = re + '\n' + 'ttl:' + str(a.ttl)
        re = re + '\n' + 'len:' + str(a.len)
        re = re + '\n' + 'data:' + a.data
    return re


# 获得RRs的list
def get_record_list(message, start, num_, time):
    ori = start
    re = []
    num = 0
    min_ttl = 2147483647
    while num < num_:
        try:
            offset = message_resolver(message, start, start + 2)
            start = start + 2
            type = str_four_hex_to_bin(message_resolver(message, start, start + 2))
            if type in type_dic:
                pass
            else:
                return [], ori, min_ttl
            start = start + 2
            cls = message_resolver(message, start, start + 2)
            start = start + 2
            ttl = str_four_bytes_hex_to_bin(message_resolver(message, start, start + 4))
            min_ttl = min(ttl, min_ttl)
            start = start + 4
            len = str_four_hex_to_bin(message_resolver(message, start, start + 2))
            start = start + 2
            data = message_resolver(message, start, start + len)
            num = num + 1
            re.append(DnsAnswerNode(offset, type, cls, ttl, len, data, time))
            start = start + len
        except IndexError:
            pass
    return re, start, min_ttl


# 解析报文的类
class DnsMessageResolver:

    # 字符串化，测试用
    def to_string(self):
        re = 'id:' + self.id + '\n'
        re = re + 'flags:' + self.flags + '\n'
        re = re + 'questions:' + str(self.questions) + '\n'
        re = re + 'answer:' + str(self.answer) + '\n'
        re = re + 'authority:' + str(self.authority) + '\n'
        re = re + 'additional:' + str(self.additional) + '\n'
        re = re + 'query_name:' + self.query_name + '\n'
        re = re + 'query_type:' + self.query_type + '\n'
        re = re + 'query_class:' + self.query_class + '\n'
        re = re + 'answers:' + list_to_str(self.answers) + '\n'
        re = re + 'authorities:' + list_to_str(self.authorities) + '\n'
        return re

    def __init__(self, message):
        self.min_ttl = 0
        self.time = datetime.datetime.now()
        self.id = message_resolver(message, 0, 2)
        self.flags = message_resolver(message, 2, 4)
        self.questions = str_four_hex_to_bin(message_resolver(message, 4, 6))
        self.answer = str_four_hex_to_bin(message_resolver(message, 6, 8))
        self.authority = str_four_hex_to_bin(message_resolver(message, 8, 10))
        self.additional = str_four_hex_to_bin(message_resolver(message, 10, 12))
        self.query_name, start = get_query_name(message)
        self.query_type = message_resolver(message, start, start + 2)
        start = start + 2
        self.query_class = message_resolver(message, start, start + 2)
        start = start + 2
        self.answers = []
        self.authorities = []
        ttl_ = 2147483647
        self.answer_message = message[start:]
        if self.answer == 0:
            pass
        else:
            self.answers, start, self.min_ttl = get_record_list(message, start, self.answer, self.time)
        if self.authority == 0:
            pass
        else:
            self.authorities, start, ttl_ = get_record_list(message, start, self.authority, self.time)
        self.min_ttl = min(self.min_ttl, ttl_)
        self.real_time = self.time
        self.time = self.time + datetime.timedelta(seconds=self.min_ttl)


# 用于存储与缓存的类
class DnsCacheNode:

        def __init__(self, dns_response):
            self.query_name = dns_response.query_name
            self.query_type = dns_response.query_type
            self.query_class = dns_response.query_class
            self.answer = dns_response.answers
            self.authority = dns_response.authorities
            self.answer_message = dns_response.answer_message
            self.time = dns_response.time
            self.answer_num = tran_into_hex_str(dns_response.answer)
            self.authority_num = tran_into_hex_str(dns_response.authority)
            self.real_time = dns_response.real_time

        # 读取缓存的时候修改缓存的ttl
        def change_ttl(self, ttl):
            re = b''
            start = 0
            l = len(self.answer_message)
            while start < l:
                try:
                    re = re + self.answer_message[start:start + 6]
                    start = start + 6
                    ttl_ = str_four_bytes_hex_to_bin(message_resolver(self.answer_message, start, start + 4))
                    re = re + trans_into_hex(tran_into_hex_str_four(ttl_ - ttl))
                    start = start + 4
                    data_len = str_four_hex_to_bin(message_resolver(self.answer_message, start, start + 2))
                    re = re + self.answer_message[start:start + 2]
                    start = start + 2
                    re = re + self.answer_message[start:start + data_len]
                    start = start + data_len
                    while start < l and self.answer_message[start:start + 1] != b'\xc0':
                        re = re + self.answer_message[start:start + 1]
                        start = start + 1
                except IndexError:
                    while start < l:
                        re = re + self.answer_message[start:start + 1]
                        start = start + 1
            self.answer_message = re
            self.real_time = datetime.datetime.now()


# 一个RR记录的类
class DnsAnswerNode:

        def __init__(self, offset, type, cls, ttl, len, data, time):
            self.offset = offset
            self.type = type
            self.cls = cls
            self.ttl = ttl
            self.len = len
            self.data = data
            self.time = time

        def compare_to_time(self):
            a = datetime.now()
            return self.ttl > (a-self.time).seconds


# 打印当前缓存的数据
def print_cache(list):
    for a in list:
        print('**************************************')
        print('QueryName: ' + a.query_name)
        print('QueryType: ' + a.query_type)
        print('QueryClass: ' + a.query_class)
        num = 1
        print(';; ANSWER SECTION:')
        for b in a.answer:
            print('%-15s%-15d%-15s%-15s%-15s' % (b.offset, b.ttl, b.cls, b.type, b.data))
        print(';; AUTHORITY SECTION:')
        for c in a.authority:
            print('%s     %d     %s     %s     %s' % (c.offset, c.ttl, c.cls, c.type, c.data))
        print('**************************************')
        print('time_to_delete: '+a.time.strftime("%Y-%m-%d %H:%M:%S"))
        print('**************************************')


# 在缓存中寻找是否有满足要求的数据
def search_cache(dns_query, dns_cache):
    for a in dns_cache:
        if a.query_name == dns_query.query_name and a.query_class == dns_query.query_class and a.query_type == dns_query.query_type:
            if a.time > datetime.datetime.now():
                a.change_ttl((datetime.datetime.now() - a.real_time).seconds)
                return True, a
            else:
                pass
    return False, None


def tran_into_hex_str_two(message):
    num = str(hex(message))
    le = 4 - len(num)
    re = '0' * le + num[2:]
    return re


# 将url地址转化为udp报文字符串
def tran_url_hex_str(message):
    re = ''
    li = message.split('.')
    key = 0
    while key < len(li):
        re = re + tran_into_hex_str_two(len(li[key]))
        for a in li[key]:
            re = re + tran_into_hex_str_two(ord(a))
        key = key + 1
    re = re + '00'
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


# 获取缓存里的数据，重组成新的dns报文
def encode_byte(dns_query, dns_cache_node):
    re = b''
    message = dns_query.id + dns_query.flags + '0001' + dns_cache_node.answer_num + dns_cache_node.authority_num + \
              '0000' + tran_url_hex_str(dns_query.query_name) + dns_cache_node.query_type + dns_cache_node.query_class
    re = trans_into_hex(message)
    re = re + dns_cache_node.answer_message
    return re


# 主程序
def main():
    server_port = 53
    server_socket = socket(AF_INET, SOCK_DGRAM)    # IPV4，udp连接
    server_socket.bind(('127.0.0.1', server_port))  # 接口绑定
    client_socket = socket(AF_INET, SOCK_DGRAM)    # 用于向服务器发送报文的接口
    dns_cache = []                                # dns缓存list
    num = 1
    while True:
        try:
            message_query, address_query = server_socket.recvfrom(4096)
            try:
                dns_query = DnsMessageResolver(message_query)
            except IndexError:
                continue
            if_contain, cache = search_cache(dns_query, dns_cache)
            if if_contain:  # 如果有可用缓存则封装
                query_response = encode_byte(dns_query, cache)
                print('ID#' + str(num) + ': Cache successfully.')
            else:  # 无可用缓存则向上游服务器发送报文，缓存在内存里
                client_socket.sendto(message_query, ('114.114.114.110', 53))
                query_response, address_response = client_socket.recvfrom(4096)
                try:
                    dns_response = DnsMessageResolver(query_response)
                except IndexError:
                    continue
                dns_cache.append(DnsCacheNode(dns_response))
                print('ID#' + str(num) + ': Get from upstream DNS resolver successfully.')
                print('ID#' + str(num) + ': Append to DNS cache successfully.')
            num = num + 1
            server_socket.sendto(query_response, address_query)
        except ConnectionResetError:
            pass


if __name__ == '__main__':
    main()
