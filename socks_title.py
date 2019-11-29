import socket
import sys
import threading
import re
import ssl
from urllib.parse import urlparse
import queue
from queue import Queue
import time

debug=0
q  = queue.Queue()
resource  = "/index.html"

def filterURL(url):
    if(url[:4] == 'http'):# {{{
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
    else:
        url = 'http://'+url
        res = urlparse(url)
        if(res.port == None):
            ret = (res.hostname, 80, 'http')
        else:
            ret = (res.hostname, res.port, 'http')
        return ret# }}}

def HTTPS_getTitle(ip, port, timeout=1 , resource = None):
    context= ssl.SSLContext(ssl.PROTOCOL_TLSv1)# {{{
    context.verify_mode=ssl.CERT_NONE
    context.check_hostname=False
    raw_payload=  "GET %s HTTP/1.1\r\nHost:%s\r\nUser-Agent: Mozilla /5.0 (Compatible MSIE 9.0;Windows NT 6.1;WOW64; Trident/5.0)\r\n\r\n"  
    if(resource != None):
        GET_payload = raw_payload% (resource, ip)
    else:
        GET_payload = raw_payload %("/", ip)

    if(ip==None):
        return
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
            if(debug == 1):
                print(byte.decode('utf-8'))
            if(byte == b''):
                break
            if( b'HTTP/1.1 30'in data and (b'Location: ' in data or b'location' in data)):
                break
            if(b'</title>'in data or b'</TITLE>' in data):
                break


            continue
    except Exception as e:
        print('('+ip+' :'+str(e)+')')
        return
    resp = data
    if(b'30' == resp[9:11]):
        if(b'Location' in resp):
            newurl = re.search("Location: .*\n", resp.decode('utf-8')).group(0)[10:-2]
        else:
            newurl = re.search("location: .*\n", resp.decode('utf-8')).group(0)[10:-2]
        if (newurl[:2] == '//'):
                newurl = newurl[2:]
        res = filterURL(newurl)
        if(res==None):
            print('('+ip+' : failed)')
        if(res[0]==None):
            print('('+ip+' : failed)')
        getTitle( res,timeout = timeout)
        return

    respstr = resp
    try:
        if(b'</title>' in  respstr):
            headstart= respstr.index(b'<title>')+7
            headend= respstr.index(b'</title>')
        else:
            headstart= respstr.index(b'<TITLE>')+7
            headend= respstr.index(b'</TITLE>')
    except:
        print('('+ip+','+respstr[:32]+','+'cant find title'+')')
        return
    try:
        title = respstr[headstart: headend].decode('utf-8')
    except:
        try:
            title = respstr[headstart: headend].decode('gb2312')
        except:
            print('('+ip+' : failed to decode( target encoding is neither gb2312 nor utf-8)')
            return
    print((ip, title, 'https://'+ip+':'+str(port), "resource: "+resource))# }}}

def HTTP_gettitle(ip, port, timeout=0.5, resource = None):
    raw_payload=  "GET %s HTTP/1.1\r\nHost:%s\r\nUser-Agent: Mozilla /5.0 (Compatible MSIE 9.0;Windows NT 6.1;WOW64; Trident/5.0)\r\n\r\n"  # {{{
    if(resource != None):
        GET_payload = raw_payload% (resource, ip)
    else:
        GET_payload = raw_payload %("/", ip)
    if(ip==None):
        return
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
        return
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
        return
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
        return
    try:
        title = respstr[headstart: headend].decode('utf-8')
    except:
        try:
            title = respstr[headstart: headend].decode('gb2312')
        except:
            print('('+ip+' : failed to decode( target encoding is neither gb2312 nor utf-8)')
            return
    print((ip, title, 'http://'+ip+':'+str(port), "resource: ", resource))# }}}


def getTitle(url_filterd, timeout=0.5 ):
    if(url_filterd[2]== 'http'):
        HTTP_gettitle(url_filterd[0], url_filterd[1], timeout= timeout, resource = resource)
    elif(url_filterd[2]== 'https'):
        HTTPS_getTitle(url_filterd[0], url_filterd[1], timeout= timeout*2, resource = resource)

def thread_cb( timeout=1):
    while(True):
        try:
            target = q.get_nowait()
            getTitle(target, timeout =timeout)
        except queue.Empty:
            if (debug ==1):
                print("Queue Empty Exiting...");
            break
    return

def timer():
    while(True):
        if((time.time()//1) %10 == 0):
            print(q.qsize()/65535)
            time.sleep(1)
       


def async_getTitle( urls=[] , timeout=0.5,thread_cnt = 256):
    #parsing http like url# {{{
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
            q.put(ret)
            continue
        else:
            url = 'http://'+url
            res = urlparse(url)
            if(res.port == None):
                ret = (res.hostname, 80, 'http')
            else:
                ret = (res.hostname, res.port, 'http')
            q.put(ret)
            continue

    #   create_threads
    connection_cnt = q.qsize() 
    threads = []
    for i in range(thread_cnt):
        threads.append(threading.Thread(target=thread_cb,kwargs={'timeout':timeout}))
        threads[i].start()
#    threading.Thread(target= timer).start()
    for i in threads:
        i.join()
        


#HTTPS_getTitle('www.taobao.com',443,2)
#async_getTitle(['www.baidu.com'],timeout=20)
#async_getTitle(['yandex.com','www.baidu.com','www.qq.com','www.taobao.com','www.cqupt.edu.cn','stackoverflow.com','google.com','apple.cn'],timeout=2)
# }}}

if __name__ == '__main__':
    f = open(sys.argv[1])
    urls = []
    thread_cnt = 256
    for i in f:
        urls.append(i[:-1])
    async_getTitle(urls, timeout=10, thread_cnt= thread_cnt)
    f.close()



