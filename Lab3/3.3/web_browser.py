import asyncio
import os
err404 = [
        b'HTTP/1.0 404 Not Found\r\n',
        b'Connection: close'
        b'Content-Type:text/html; charset=utf-8\r\n',
        b'\r\n',
        b'<html><body>404 Not Found<body></html>\r\n',
        b'\r\n'
    ]
err405 = [
        b'HTTP/1.0 405 Method Not Allowed\r\n',
        b'Connection: close'
        b'Content-Type:text/html; charset=utf-8\r\n',
        b'<html><body>405 Not Allowed<body></html>\r\n',
        b'\r\n'
    ]
sorry = [
        b'HTTP/1.0 200 OK\r\n',
        b'Content-Type:text/html; charset=utf-8\r\n',
        b'Connection: close\r\n',
        b'\r\n',
        b'<html><body>Sorry, the browser cannot read this file<body></html>\r\n',
        b'\r\n'
    ]
head = [
        b'HTTP/1.0 200 OK\r\n',
        b'Content-Type:text/html; charset=utf-8\r\n',
        b'Connection: close\r\n',
        b'\r\n'
    ]
index = 'Index of ./'

def generateHref(list,url):
    urls=url.split("/")
    split=""
    url1='/'
    key=1
    result=''
    while(True):
        if(key==urls.__len__()-1):
            break
        url1 = url1 + urls[key]
        key=key+1
    if url.split("/")[1]!="":
        split="/"
        result = '<a href=\"..'+url1+'\">../</a><br>'
    for a in list:
        result = result + "<a href=\"" + url + split + a + "\">" + a + "</a><br>"
    return result

async def browser(reader, writer):
    firstLine = await reader.readline()

    method = firstLine.decode().split(' ')[0]
    url = ''
    try:
        url = firstLine.decode().split(' ')[1]
    except IndexError:
        pass

    if method != "GET":
        writer.writelines(err405)
        await writer.drain()
        writer.close()
    else:
        try:
            jug = os.path.isfile('.'+url)
            if(jug == False):
                href=generateHref(os.listdir('./'+url),url)
                index1 =index + url
                content=[
                    b'HTTP/1.0 200 OK\r\n',
                    b'Content-Type:text/html; charset=utf-8\r\n',
                    b'Connection: close\r\n',
                    b'\r\n',
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
                    b'</body></html>\r\n',
                ]
                writer.writelines(content)
            else:
                file = open('.'+url)
                lenth =str(os.path.getsize('./' + url))
                contents=''
                try:
                    contents = file.read()
                    content = [
                        b'HTTP/1.0 200 OK\r\n',
                        b'Content-Type:text/html; charset=utf-8\r\n',
                        b'Connection: close\r\n',
                        b'\r\n',
                        b'<html><head><title>',
                        (index + url).encode('utf-8'),
                        b'</title></head>\r\n',
                        b'<body bgcolor="white">\r\n',
                        b'<h1>\r\n',
                        b'Path:' + url.encode('utf-8'),
                        b'</h1>\r\n',
                        b'<h2>\r\n',
                        b'Size:' + lenth.encode('utf-8'),
                        b'</h2>\r\n',
                        b'<pre>\r\n',
                        b'<code>\r\n',
                        contents.encode('utf-8'),
                        b'</code>\r\n',
                        b'</pre>\r\n',
                        b'</body></html>\r\n',
                    ]
                    writer.writelines(content)
                except:
                    writer.writelines(sorry)


        except FileNotFoundError:
            writer.writelines(err404)
        await writer.drain()
        writer.close()
        # while True:
        #     data = await reader.readline()
        #     message = data.decode().split(' ')
        #     print(data)
        #     if data == b'\r\n':
        #         break




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
