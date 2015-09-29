#!/usr/bin/python
# -*- encoding: utf-8 -*-
import llsif_parser
import logging, os, sys,codecs
import time, datetime, json, hashlib
import config
import account
import datetime as dt
import re

root = config.ROOT
index_list = dict( TW = [u'公告',u'異常',u'更新'],
                   JP = [u'お知らせ', u'不具合', u'アップデート'],
                   EN = [u'Notifications', u'Errors', u'Updates'])

class Worker:
    parser = None
    logger = None

    def __init__(self, version, ostype):
        self.version = version
        self.os = ostype
        self.parser = llsif_parser.parser(version, ostype)
        self.git = account.INFO[version]["GIT"]
        self.folder = root + account.INFO[version]["FOLDER"]
        self.path = os.path.dirname(self.folder + 'content/')
        logging.basicConfig(filename=root+"logs_%s" %version,level=logging.INFO)
        self.logger = logging.getLogger('main')

    def upload_img(self, url):
        try:
            url = "http://" + url.split('//')[1]
        except:
            return url
        self.logger.info("Download image file: %s" %url)
        filename = url.split('/')[-1]
        if 'vote_icon' in filename:
            try:
                filename = re.findall(r"/vote/(\w+)/icon/", s)[0] + filename
            except:
                pass
        try:
            if not os.path.exists(self.path + '/images/' + filename):
                os.system('wget %s -P %s' %(url, self.path + '/images/' ))
            return self.git + 'images/' + filename
        except:
            self.logger.info("Error: Fail to download image: %s" %url)
            return url #client.upload_from_url(url)['link']

    def check_link(self, link):
        #link = link.decode("utf-8").replace('native://browser?url=', '').encode("utf-8")
        if u"native:" in link: link = link[21:]
        announce_id = re.findall(r'announce_id=(\d+)', link)
        if announce_id:
            link = self.git + 'announce_%s.html' %announce_id[0]
        static_id = re.findall(r'static\?id=(\d+)', link)
        if static_id:
            link = self.git + 'pages/static_%s.html' %static_id[0]
            self.SavePage("static", static_id[0])
        return link

    def push_github(self, post, update, remove, string=""):
        if post:
            string += ' [POST] ' + ','.join(post[:5])
        if update:
            string += ' [UPDATE] ' + ','.join(update[:5])
        if remove:
            string += ' [REMOVE] ' + ','.join(remove[:5])
        os.chdir(self.folder)
        os.system("make html")
        os.system("~/.local/bin/ghp-import -p output -m '%s'" %string)

    def SavePage(self, ptype , pid):
        time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        filename = os.path.join( self.path, 'pages/%s_%s.md' %(ptype,pid))
        title, date, detail = self.parser.page_detail(ptype, pid)
        for img in detail.findAll('img'):
            img['src'] = self.upload_img(img['src']) 
        for url in detail.findAll('a'):
            try:    
                url['href'] = self.check_link(url['href'])
            except:
                pass
        with codecs.open(filename,'w','utf-8') as file:
            file.write(u'Title: %s\n' %title)
            file.write(u'Date: %s\n' %date)
            file.write(u'Modify: %s\n' %time_now)
            file.write(u'Slug: %s_%s\n' %(ptype,pid))
            file.write(u'\n')
            file.write(u'%s\n' %detail)


    def InsertNews(self):
        self.logger.info("start main() // %s" %time.strftime("%c"))
        lPost, lUpdate,lRemove = [], [], [] 
        hashlist = {}
        with open(self.folder + "filelog.json", 'r') as outfile:
            hashlist = json.load(outfile)

        time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        pidlist = []
        for index in xrange(3):
            index_type = index_list[self.version][index]
            old_offset, offset = 0, 0
            while True:
                for pid,title,date,content,img,offset in self.parser.web_view(index, offset):
                    pidlist.append(pid)
                    filename = os.path.join( self.path, 'announce_%s.md' %pid)
                    md5_title = hashlib.md5(title.encode('utf-8')).hexdigest()
                    md5_content = hashlib.md5(content.encode('utf-8')).hexdigest()
                    try:
                        if (pid not in hashlist):
                            status = "post"
                        elif not (md5_title == hashlist[pid]['title']) or \
                             not (md5_content == hashlist[pid]['content']):
                            status = "update"
                        elif hashlist[pid].get("remove_time"):
                            status = "reback"
                        else:
                            hashlist[pid].setdefault("oslist",[])
                            if self.os not in hashlist[pid]["oslist"]:
                                hashlist[pid]["oslist"].append(self.os) 
                            continue
                        self.logger.info("Fetch file: %s %s" %(pid, title))
                        if img:
                            img = self.upload_img(img)
                            content = u'<img src="%s"> %s' %(img,content)
                        detail = self.parser.web_detail(index, pid)
                        md5_detail = hashlib.md5(''.join(detail.text.encode('utf-8').split())).hexdigest()
                        
                        for img in detail.findAll('img'):
                            img['src'] = self.upload_img(img['src']) 
                        for url in detail.findAll('a'):
                            url['href'] = self.check_link(url['href'])

                        with codecs.open(filename,'w','utf-8') as file:
                            file.write(u'Title: %s\n' %title)
                            file.write(u'Date: %s\n' %date)
                            file.write(u'Modify: %s\n' %time_now)
                            file.write(u'Category: %s\n' %index_type)
                            file.write(u'Tags: POST\n' )
                            file.write(u'Slug: announce_%s\n' %pid)
                            file.write(u'Summary: %s\n' %content)
                            file.write(u'\n')
                            file.write(u'%s\n' %detail)
                
                        self.logger.info("Fetch file: %s %s success!" %(pid,title))
                        hashlist.setdefault(pid, {})
                        oslist = set(hashlist.get("oslist", []))
                        oslist.add(self.os)
                        hashlist[pid].update(dict(
                                              oslist = list(oslist), 
                                              index = index,
                                              title = md5_title,
                                              content = md5_content,
                                              detail = md5_detail))
                        if status == "post":
                            lPost.append(pid)
                            hashlist[pid]["create_time"] = time_now
                        if status == "modify":
                            lUpdate.append(pid)
                            hashlist[pid]["modify_time"] = time_now
                        if status == "reback":
                            lUpdate.append(pid)
                            hashlist[pid].pop("remove_time")
                            hashlist[pid]["modify_time"] = time_now
                    except Exception as e:
                        print str(e)
                        self.logger.info("Error: %s %s, %s" %(pid,title,str(e)))
                        continue

                offset = int(str(offset))
                if offset == old_offset:
                    break
                old_offset = offset

        # remove old announce
        if pidlist:
            for pid in hashlist:
                if hashlist[pid].get("remove_time"): continue
                if self.os not in hashlist[pid].get("oslist",[]): continue
                if pid not in pidlist:
                    filename = os.path.join( self.path, 'announce_%s.md' %pid)
                    os.system("sed -i 's/Tags: .*$/Tags: REMOVE/g' %s" %filename)
                    hashlist[pid]['remove_time'] = time_now
                    lRemove.append(pid)
                    self.logger.info("Remove old announce: %s" %pid)

        # save filelog
        with open(self.folder + "filelog.json" , 'w') as outfile:
            json.dump(hashlist, outfile)

        self.logger.info("end main() // %s" %time.strftime("%c"))
        return lPost, lUpdate, lRemove

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'no argument'
        sys.exit()

    version, ostype = sys.argv[1], "Android"
    if version not in ("TW","EN","JP"):
        print 'invalid argument'
        sys.exit()
    if dt.datetime.today().hour % 2:
        ostype = "iOS"
    
    worker = Worker(version, ostype)
    lPost, lUpdate, lRemove = worker.InsertNews()
    if len(lPost) + len(lUpdate) + len(lRemove) > 0:
        worker.push_github(lPost, lUpdate, lRemove)
