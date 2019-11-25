import socket
import sys
import threading
import re
import ssl
from urllib.parse import urlparse


def filterURL(url):
    if(url[:4] == 'http'):
        try:
            res =urlparse(url)
        except:
            return None
        if(res.port == None and res.scheme == 'https'):
                ret = (res.hostname,443, 'https') 
        elif(res.port == None and res.scheme == 'http'):
                ret = (res.hostname, 80, 'http')
        else:
                ret = (res.hostname, res.port, res.scheme)
        return ret
#    elif( re.search('^[0-9]*\.',url)):
    else:
        url = 'http://'+url
        res = urlparse(url)
        if(res.port == None):
            ret = (res.hostname, 80, 'http')
        else:
            ret = (res.hostname, res.port, 'http')
        return ret

def HTTPS_getTitle(ip, port, timeout=1):
    context= ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    context.verify_mode=ssl.CERT_NONE
    context.check_hostname=False
    GET_payload=  "GET / HTTP/1.1\r\nHost:%s\r\n\r\n" % ip
    if(ip==None):
        exit()
    try:
        sock = socket.create_connection((ip, port), timeout=1)
        soc = context.wrap_socket(sock, server_hostname=ip)
        soc.settimeout(timeout)
        soc.send(GET_payload.encode())
        data = b''
        byte = b''
        while( 1):
            byte = soc.recv(768)
            data+=byte
            if(byte == b''):
                break
            if( b'HTTP/1.1 30'in data and (b'Location: ' in data or b'location' in data)):
                break
            if(b'</title>'in data or b'</TITLE>' in data):
                break


            continue
    except Exception as e:
        print('('+ip+' :'+str(e)+')')
        sys.exit()
    resp = data
    if(b'30' == resp[9:11]):
        if(b'Location' in resp):
            newurl = re.search("Location: .*\n", resp.decode('utf-8')).group(0)[10:-2]
        else:
            newurl = re.search("location: .*\n", resp.decode('utf-8')).group(0)[10:-2]
        res = filterURL(newurl)
        if(res==None):
            print('('+ip+' : failed)')
        if(res[0]==None):
            print('('+ip+' : failed)')
        getTitle( res,timeout = timeout)
        exit()

    respstr = resp
    try:
        if(b'</title>' in  respstr):
            headstart= respstr.index(b'<title>')+7
            headend= respstr.index(b'</title>')
        else:
            headstart= respstr.index(b'<TITLE>')+7
            headend= respstr.index(b'</TITLE>')
    except:
        print('('+ip+' : failed to find <title> tag)')
        exit()
    try:
        title = respstr[headstart: headend].decode('utf-8')
    except:
        title = respstr[headstart: headend].decode('gb2312')

    print((ip, title, 'https://'+ip+':'+str(port)))

def HTTP_gettitle(ip, port, timeout=0.5):
    GET_payload=  "GET / HTTP/1.1\r\nHost:%s\r\n\r\n" % ip
    if(ip==None):
        exit()
    try:
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soc.settimeout(timeout)
        soc.connect((ip, port))
        soc.send(GET_payload.encode())
        data = b''
        byte = b''
        while(True):
            byte = soc.recv(768)
            data+=byte
        #    print(data.decode('utf-8'))
            if(byte == b''):
                break
            if( b'HTTP/1.1 30'in data and (b'Location: ' in data or b'location' in data)):
                break
            if(b'</title>'in data or b'</TITLE>' in data):
                break
    except Exception as e:
        print('('+ip+' :'+str(e)+')')
        sys.exit()
    resp = data
    if(b'30' == resp[9:11]):
        if(b'Location' in resp):
            newurl = re.search("Location: .*\n", resp.decode('utf-8')).group(0)[10:-2]
        else:
            newurl = re.search("location: .*\n", resp.decode('utf-8')).group(0)[10:-2]
        res = filterURL(newurl)
        if(res == None):
            print('('+ip+' : failed)')
        if(res[0]==None):
            print('('+ip+' : failed)')
        getTitle( res,timeout = timeout)
        exit()
    respstr = resp
    try:
        if(b'</title>' in  respstr):
            headstart= respstr.index(b'<title>')+7
            headend= respstr.index(b'</title>')
        else:
            headstart= respstr.index(b'<TITLE>')+7
            headend= respstr.index(b'</TITLE>')
    except Exception as e:
        print('('+ip+' : failed to find <title> tag)')
        exit()
    try:
        title = respstr[headstart: headend].decode('utf-8')
    except:
        title = respstr[headstart: headend].decode('gb2312')

    print((ip, title, 'http://'+ip+':'+str(port)))


def getTitle(url_filterd, timeout=0.5 ):
    if(url_filterd[2]== 'http'):
        HTTP_gettitle(url_filterd[0], url_filterd[1], timeout= timeout)
    elif(url_filterd[2]== 'https'):
        HTTPS_getTitle(url_filterd[0], url_filterd[1], timeout= timeout*2)

def async_getTitle( urls=[] , timeout=0.5,thread_cnt = 256):
    #parsing http like url
    connections = []
    for url in urls:
        if(url[:4] == 'http'):
            try:
                res =urlparse(url)
            except:
                continue
            if(res.port == None and res.scheme == 'https'):
                    ret = (res.hostname,443, 'https') 
            elif(res.port == None and res.scheme == 'http'):
                    ret = (res.hostname, 80, 'http')
            else:
                    ret = (res.hostname, res.port, res.scheme)
            connections.append(ret)
            continue
    #    elif( re.search('^[0-9]*\.',url)):
        else:
            url = 'http://'+url
            res = urlparse(url)
            if(res.port == None):
                ret = (res.hostname, 80, 'http')
            else:
                ret = (res.hostname, res.port, 'http')
            connections.append( ret)
            continue

#   create_threads
    connection_cnt = len(connections)
    if(connection_cnt % thread_cnt == 0):
        r_cnt = connection_cnt//thread_cnt
    else:
        r_cnt = connection_cnt//thread_cnt +1
    for n_round in range(r_cnt):
        threads = []
        for j in range(thread_cnt):
            if(n_round*thread_cnt+j >= connection_cnt):
                break
            print({'ip':connections[n_round*thread_cnt+j][0],'port':connections[n_round*thread_cnt+j][1],'timeout':timeout})
            threads.append(threading.Thread(target=getTitle,kwargs={'url_filterd':connections[n_round*thread_cnt+j],'timeout':timeout}))
        for thr in threads:
            thr.start()
        for thr in threads:
            thr.join(timeout=20)
        threads.clear()

#HTTPS_getTitle('www.taobao.com',443,2)
#async_getTitle(['www.baidu.com'],timeout=20)
#async_getTitle(['yandex.com','www.baidu.com','www.qq.com','www.taobao.com','www.cqupt.edu.cn','stackoverflow.com','google.com','apple.cn'],timeout=2)

if __name__ == '__main__':
    f = open(sys.argv[1])
    urls = []
    thread_cnt = 256
    for i in f:
        urls.append(i[:-1])
    async_getTitle(urls, timeout=10, thread_cnt= thread_cnt)



