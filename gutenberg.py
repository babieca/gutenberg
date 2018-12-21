import re
import os
import sys
import requests
import time
from bs4 import BeautifulSoup as bs
import io
import zipfile
from urllib.parse import urlparse, urljoin
import random

def create_directory(dirname):
    if not os.path.exists(dirname):
        try:
            os.makedirs(dirname)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise ValueError(("The directory '{}' was created " +
                    "between the os.path.exists and the os.makedirs").
                    format(dirname))
    return True


def random_line(fname):
    
    with open(fname) as f:
        content = f.readline()
    
    content = [x.strip() for x in content]
    
    return random.choice(content)


def fetch_url(url, useragents_file=None):
    headers = None
    if useragents_file:
        random_useragent = random_line(useragents_file)
        headers = {'User-Agent': random_useragent}
        
    return requests.get(url, headers)


def is_absolute(url):
    return bool(urlparse(url).netloc)


if __name__ == '__main__':

    time_sleep = 3
    #extensions = ('.txt', '.pdf')
    extensions = '.pdf'
    directory = './files'
    useragent_file = './user-agents.txt'
    url = 'http://www.gutenberg.org/robot/harvest?offset=254442&filetypes[]=pdf&langs[]=en'
    regex_zipfiles = 'http://aleph.gutenberg.org/.*\.zip'
    regex_nextpage = 'harvest\?offset\=\d+\&filetypes\[\]\=pdf\&langs\[\]\=en'
    
    if not os.path.isabs(directory):
        directory = os.path.abspath(directory)
    
    create_directory(directory)
    
    while url:
        
        print("Requesting url: '{}'".format(url))
        
        resp = fetch_url(url, useragent_file)
        soup =  bs(resp.content, 'lxml')
        
        url = None
        links_zipfiles = []
        for link in soup.find_all('a', href=True):
            if re.search(regex_zipfiles, link['href']):
                links_zipfiles.append(link['href'])
                
            if re.search(regex_nextpage, link['href']):
                url = link['href']
                url = url if is_absolute(url) else urljoin('http://aleph.gutenberg.org/', url)
        
        
        for link_zipfile in links_zipfiles:
            resp = fetch_url(link_zipfile, useragent_file)
            zip_file = zipfile.ZipFile(io.BytesIO(resp.content))
            for file in zip_file.namelist():
                if file.endswith(extensions):
                    print("|--- url: '{}' extracting file: '{}'".format(link_zipfile, file))
                    zip_file.extract(file, directory)
            zip_file.close()
            time.sleep(time_sleep)
        
        time.sleep(time_sleep)
        
    sys.exit(0)