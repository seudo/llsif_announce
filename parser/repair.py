'''
 If the content folder is removed... we can use the script to regenerate md file from output html files ._,
'''

from os import listdir
from os.path import isfile, join
from BeautifulSoup import BeautifulSoup
import sys, codecs, json

mdpath = 'content'
htmlpath = 'output'

summaries = {}
def parse_from_index():
    for idx in xrange(1,5):
        if idx == 1: idx = ''
        html = open('%s/index%s.html' %(htmlpath,idx) ).read()
        soup = BeautifulSoup(html)
        for article in soup.findAll("article"):
            slug =  article.a['href'].split('/')[-1][:-5]
            summary = article.div.p.contents[0]
            summaries[slug] = summary

def save_file(filename, content):
    with codecs.open(filename, 'w', 'utf-8') as file:
        content)

def parse_from_output():
    mdfiles = [ f.split('.')[0] for f in listdir(mdpath) if isfile(join(mdpath,f)) ]
    htmlfiles = [ f.split('.')[0] for f in listdir(htmlpath) if isfile(join(htmlpath,f)) and 'announce' in f ]

    for slug in set(htmlfiles) - set(mdfiles):
        html = open('%s/%s.html' %(htmlpath,slug) ).read()
        soup = BeautifulSoup(html)

        title = soup.find("meta", {"property":"og:title"})['content']
        category = soup.find("meta", {"property":"article:section"})['content']
        date = soup.find("meta", {"property":"article:published_time"})['content']
        tags = soup.find("meta", {"property":"article:tag"})['content']
        summary = soup.find("meta", {"property":"og:description"})['content']   # without html tag (image)
        detail = soup.find("div", {"class": "content_news"})
        yield slug, title, category, date, tags, summary, detail

if __name__ == "__main__":
    parse_from_index()
    for slug, title, category, date, tags, summary, detail in parse_from_output():
        filename = '%s.md' %slug
        summary = summaries[slug]
        content =  (u'Title: {0}\n'
                    u'Date: {1}\n'
                    u'Modify: {1}\n'
                    u'Category: {2}\n'
                    u'Tags: {3}\n'
                    u'Slug: {4}\n'
                    u'Summary: {5}\n\n'
                    u'{6}\n').format(title, date, category, tags, slug, summary, detail)
        save_file(filename, content)

