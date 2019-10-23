import asyncio
import os
import time
import datetime

index = 'Index of ./'
chunk_size = 512
end = b'\r\n'


def get_last_modified(url):
    file_mt = time.localtime(os.stat(url).st_mtime)
    return time.strftime("%a, %d %b %Y %H:%M:%S GMT", file_mt)


def get_local_time():
    localtime = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.localtime())
    return localtime


def get_prv_time():
    now_time = datetime.datetime.now()
    last_time = now_time + datetime.timedelta(hours=-4)
    return last_time.strftime("%a, %d %b %Y %H:%M:%S GMT")


class Head:
    state_exp = {200: 'OK',
                 206: 'Partial Content',
                 404: 'Not Found',
                 405: 'Method Not Allowed',
                 302: 'Found'}

    def __init__(self, state):
        str = 'HTTP/1.1 %d %s\r\n' % (state, Head.state_exp[state])
        self.header = []
        self.header.append(str.encode('utf-8'))
        self.header.append('Content-Type: text/html; charset=utf-8\r\n'.encode('utf-8'))
        if state == 200 or state == 404 or state == 302:
            self.header.append('Connection: close\r\n'.encode('utf-8'))
        elif state == 206:
            self.header.append('Connection: keep-alive\r\n'.encode('utf-8'))
        self.add_head('Accept-Ranges', 'bytes')
        self.add_head('Date', get_local_time())

    def add_head(self, key, value):
        s = '%s: %s\r\n' % (key, value)
        self.header.append(s.encode('utf-8'))

    def close_head(self):
        self.header.append('\r\n'.encode('utf-8'))


class GetHead:
    def __init__(self, url, method, range, partial_content):
        self.url = url
        self.method = method
        self.range = range
        self.partial_content = partial_content
        self.cookie_if = False
        self.last_dir = ''

    def add_cookie(self, last_dir):
        self.cookie_if = True
        self.last_dir = last_dir

    def get_last_dir(self):
        return self.last_dir


def file_reader(writer, fo, start, end):
    fo.read(int(start))
    need = int(end) - int(start) + 1
    while True:
        if need > 2048:
            step = 2048
        else:
            step = need
        need = need - step
        file_data = fo.read(step)
        if file_data:
            writer.write(file_data)
        else:
            break
    fo.close()


def generate_href(list, url):
    urls = url.split("/")
    split = ""
    url1 = ''
    key = 1
    result = '<h3>File folder</h3>'
    file_folder = []
    file = []
    while True:
        if key == urls.__len__()-1:
            break
        url1 = url1 + '/' +urls[key]
        key = key + 1
    if url.split("/")[1] != "":
        split = "/"
        if url1 == "":
            result = result + '<a href="http://127.0.0.1:8080//">../</a><br>'
        else:
            result = result + '<a href=\"'+url1+'\">../</a><br>'
    for a in list:
        url2 = url + split + a
        if os.path.isfile('.' + url2):
            file.append("<a href=\"" + url + split + a + "\">" + a + "</a><br>")
        else:
            file_folder.append("<a href=\"" + url + split + a + "\">" + a + "</a><br>")
    for b in file_folder:
        result = result + b
    result = result + '<h3>File</h3>'
    for c in file:
        result = result + c
    return result


def generate_web(url):
    href = generate_href(os.listdir('.' + url), url)
    index1 = index + url
    content = [
        b'<html><head><title>',
        index1.encode('utf-8'),
        b'</title></head>\r\n',
        b'<body bgcolor="white">\r\n',
        b'<h1>\r\n',
        index1.encode('utf-8'),
        b'</h1><hr>\r\n',
        b'<pre>\r\n',
        href.encode('utf-8'),
        b'</pre>\r\n',
        b'<hr>\r\n',
        # b'<video src=\"test.webm\" controls=\"controls\">\r\n',
        b'</video>\r\n',
        b'</body></html>\r\n',
    ]
    return content


async def browser(reader, writer, get_=None):
    first_line = await reader.readline()
    method = first_line.decode().split(' ')[0]
    url = ''
    try:
        url = first_line.decode().split(' ')[1]
    except IndexError:
        pass
    partial_content = False
    cookie_if = False
    arr = ''
    range = []
    while True:
        data = await reader.readline()
        message = data.decode().split(': ')
        if message[0] == 'Range':
            partial_content = True
            i = 0
            uu = message[1].split('\r\n')[0].split('=')[1].split(', ')
            try:
                while True:
                    range = range + uu[i].split('-')
                    i = i + 1
            except:
                pass
            x = 0
            while x < range.__len__():
                if range[x] == '':
                    del range[x]
                x = x + 1
        elif message[0] == 'Cookie' and message[1] != "last_dir=/\r\n":
            cookie_if = True
            last_dir = message[1].split('=')[1]
        if data == b'\r\n' or data == b'':
            break
    get_head = GetHead(url, method, range, partial_content)
    if cookie_if:
        get_head.add_cookie(last_dir)
    if get_head.method == 'HEAD':
        head = Head(200)
        head.close_head()
        writer.writelines(head.header)
        await writer.drain()
        writer.close()
    elif get_head.method != "GET":
        head = Head(405)
        head.close_head()
        writer.writelines(head.header)
        await writer.drain()
        writer.close()
    elif get_head.url == "//":
        head = Head(302)
        head.add_head('Set-Cookie', "last_dir=/;")
        head.add_head('Location', "http://127.0.0.1:8080/")
        head.close_head()
        writer.writelines(head.header)
    else:
        print(get_head.url)
        if get_head.url == '/':
            if get_head.cookie_if:
                head = Head(302)
                head.add_head('Location', get_head.get_last_dir())
                head.close_head()
                writer.writelines(head.header)
            else:
                head = Head(200)
                head.close_head()
                writer.writelines(head.header)
                writer.writelines(generate_web(get_head.url))
        else:
            try:
                arrs = get_head.url.split('?')
                url = arrs[0]
                jug = os.path.isfile('.' + url)
                if jug:
                    u = url.split('/')
                    # file_name = u[u.__len__() - 1]
                    try:
                        fo = open('.' + url, 'rb')
                        size = os.path.getsize(os.path.join('.' + url))
                    except:
                        pass
                    if get_head.partial_content:
                        print(size)
                        print(get_head.range[0])
                        print(get_head.range.__len__())
                        if get_head.range.__len__() == 1:
                            end = int(size) - 1
                            head = Head(200)
                            length = int(size) - int(get_head.range[0])
                            content_range = 'bytes %s-%s/%s' % (get_head.range[0], end, size)
                            head.add_head('Content-Range', content_range)
                            head.add_head('Content-Length', str(length))
                            head.add_head('Content-Disposition', 'attachment')
                            head.add_head('Last-Modified', get_last_modified('.' + url))
                            head.close_head()
                            writer.writelines(head.header)
                            file_reader(writer, fo, get_head.range[0], str(end))
                            writer.write(b'\r\n')
                        elif get_head.range.__len__() == 2:
                            head = Head(206)
                            length = int(get_head.range[1]) - int(get_head.range[0])
                            content_range = 'bytes %s-%s/%s' % (get_head.range[0], get_head.range[1], size)
                            head.add_head('Content-Range', content_range)
                            head.add_head('Content-Length', str(length))
                            head.add_head('Content-Disposition', 'attachment')
                            head.add_head('Last-Modified', get_last_modified('.' + url))
                            head.close_head()
                            writer.writelines(head.header)
                            file_reader(writer, fo, get_head.range[0], get_head.range[1])
                            writer.write(b'\r\n')
                    else:
                        head = Head(200)
                        head.add_head('Content-Length', size)
                        head.add_head('Content-Disposition', 'attachment')
                        head.add_head('Last-Modified', get_last_modified('.' + url))
                        head.close_head()
                        writer.writelines(head.header)
                        file_reader(writer, fo, 0, size - 1)
                        writer.write(b'\r\n')
                else:
                    try:
                        os.listdir('.' + url)
                        head = Head(200)
                        last_dir = 'last_dir=' + get_head.url + '; Path=/;'
                        head.add_head('Set-Cookie', last_dir)
                        head.close_head()
                        writer.writelines(head.header)
                        writer.writelines(generate_web(get_head.url))
                    except:
                        head = Head(404)
                        head.close_head()
                        writer.writelines(head.header)
            except FileNotFoundError:
                head = Head(404)
                head.close_head()
                writer.writelines(head.header)
            try:
                await writer.drain()
                writer.close()
            except:
                pass


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(browser, '127.0.0.1', 8080, loop=loop)
    server = loop.run_until_complete(coro)

    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
