#!/usr/bin/python
# -*- encoding: utf-8 -*-

import time
import datetime as dt
import requests
import config
import account
from BeautifulSoup import BeautifulSoup, Comment
import re
import codecs

def encode_multipart_formdata(data):
    """
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = "----------------------------75f33eae1a4a"
    CRLF = '\r\n'
    L = []
    L.append('--'+BOUNDARY)
    L.append('Content-Disposition: form-data; name="request_data"')
    L.append('')
    L.append(data)
    L.append('--'+BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

class parser:
    token = ""
    payload = {}

    def __init__(self, version="TW", ostype="Android"):
        self.version = version
        self.INFO = account.INFO[version]
        self.URL = self.INFO["URL"]
        self.payload = config.HEADER
        self.payload["Host"] = self.URL.replace("http://","")
        self.payload["User-ID"] = self.INFO["UserID"]
        self.payload["Application-ID"] =  self.INFO["ApplicationID"]
        self.payload.update(config.Platform[ostype])
        self.token = self.login_authkey()

    # TODO
    def get_hmac(self, data=''):
        msg = self.INFO["LOGIN_MSG"] %(self.INFO["LOGIN_KEY"], self.INFO["LOGIN_PW"])
        hmac = self.INFO["LOGIN_HASH"] 
        return hmac 

    def get_header(self, data=''):
        ts = int(time.time())
        payload = self.payload.copy()
        payload["Authorize"] = "consumerKey=lovelive_test&timeStamp=%s&version=1.1" %ts
        if self.token: 
            payload["Authorize"] += "&token=%s" % self.token
        payload["Content-Length"] = len(data)
        if data: 
            payload["X-Message-Code"] = self.get_hmac(data)
        return payload


    def login_authkey(self):
        url = self.URL + config.URI['authkey']
        header = self.get_header()
        response = requests.post(url, data="",headers=header).json()
        if response["status_code"] == 200:
            time.sleep(3)
            self.token = response["response_data"]["authorize_token"]
            data = self.INFO["LOGIN_MSG"] %(self.INFO["LOGIN_KEY"], self.INFO["LOGIN_PW"])
            if self.INFO.get("LOGIN_HEX"): 
                data = self.INFO["LOGIN_HEX"].decode('hex')
            content_type, body = encode_multipart_formdata(data)
            url = self.URL + config.URI['login']
            header = self.get_header(data)
            header["Content-Type"] = content_type
            final = requests.post(url, data=body,headers=header).json()
            if final["status_code"] == 200:
                return final["response_data"]["authorize_token"]
        return None

    # web_index=0 announce
    # web_index=1 error
    # web_index=2 update
    def web_view(self, idx = 0, offset = 0):
        url = self.URL + config.URI['web_index'] %idx
        if offset > 0:
            url = self.URL + "/webview.php/announce/partial?disp_faulty=%s&offset=%s" %(idx,offset)
        header = self.get_header()
        response = requests.get(url, headers=header)
        response.encoding = "utf-8"
        html = BeautifulSoup(response.text)
        
        if self.version in ["TW"]:
            strSplit = u'※點擊.*詳情'
            announce_list = html.findAll('a')
        elif self.version == "EN":
            strSplit = u'Tap this notice for more details'
            announce_list = html.findAll('a')
        elif self.version == "JP":
            strSplit = u'※タップで.*ください'
            announce_list = html.findAll('div',{'class':'announce-item'})
        for url in announce_list:
            announce_id = re.findall(r'announce_id=(\d+)', url.get('data-url', url.get('href',0)))
            if announce_id:
                try:
                    img = url.find('img')['src'] if  url.find('img') else ""
                    pid = announce_id[0]
                    title = url.find('div',{'class':'title_news_all fs30'}).text
                    offset = url.get('data-disp-order', offset)
                    content =  url.find('div',{'class':'content_all'}).text
                    date = re.findall(r'(\d{4}/\d+/\d+)', content)
                    date = date[-1] if date else "2014/01/01"
                    content = re.split(strSplit, content)[0]
                    yield pid,title,date,content,img, offset
                except Exception as e:
                    print 'Error:' ,announce_id, str(e)
                    continue

    # page view
    def page_detail(self, ptype , pid=1):
        if ptype == "voting":
            url = self.URL + '/webview.php/voting/detail?id=&uid=%s' %pid
            #url = self.URL + '/webview.php/voting/index?id=%s' %pid
            #url = self.URL + "/webview.php/voting/situation?id=9&uid=3%d" %pid
            #url = self.URL + "/webview.php/voting/detail?id=9&uid=3%d&sid=%d" %(pid, sid)
        else:
            url = self.URL + config.URI['page_detail'] %pid 
        header = self.get_header()
        response = requests.get(url, headers=header)
        response.encoding = "utf-8"
        html = BeautifulSoup(response.text)
        try:
            title = html.title.text
        except:
            title = "%s_%s" %(ptype, pid)

        if self.version == "TW":
            content =  html.find('div',{'class':'main_content'})
        else:
            content =  html.find('div',{'class':'content'})
        
        if not content:
            content = html.find('body')
        [ x.extract() for x in content.findAll('h1')]
        [ x.extract() for x in content.findAll('div', {'class':"footer"})]
        [ x.extract() for x in content.findAll('a', {'id':"back"})]
        [ x.extract() for x in content.findAll('a', {'id':"back-bottom"})]
        date = re.findall(r'(\d+/\d+/\d+)', content.text)
        date = date[-1] if date else "2014/01/01"
        return title, date, content

    def web_detail(self, index=0, announce_id=0):
        url = self.URL + config.URI['web_detail'] %(announce_id, index)
        header = self.get_header()
        response = requests.get(url, headers=header)
        response.encoding = "utf-8"
        html = BeautifulSoup(response.text)
        content = html.find('div',{'class':'content_news'})
        [ x.extract() for x in content.findAll('a', {'id':"back"})]
        [ x.extract() for x in content.findAll('a', {'id':"back-bottom"})]
        return content


