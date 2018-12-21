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
import logging

LOGGERNAME = 'gutenberg'
loglevel = logging.INFO
logfile_path = './logs.log'

formatter = logging.Formatter(
    ('%(asctime)s.%(msecs)03d - %(levelname)s - ' +
    '[%(filename)s:%(lineno)d] #  %(message)s'),
    '%Y-%m-%d:%H:%M:%S')

logger = logging.getLogger(LOGGERNAME)
logger.setLevel(loglevel)

sHandler = logging.StreamHandler(stream=sys.stdout)
sHandler.setLevel(loglevel)
sHandler.setFormatter(formatter)

fHandler = logging.FileHandler(logfile_path, encoding='utf-8') #, mode='w')
fHandler.setLevel(loglevel)
fHandler.setFormatter(formatter)

logger.addHandler(sHandler)
logger.addHandler(fHandler)


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

    time_sleep_sec = 15
    #extensions = ('.txt', '.pdf')
    extensions = '.pdf'
    directory = './gutenberg'
    useragent_file = './user-agents.txt'
    url = 'http://www.gutenberg.org/robot/harvest?offset=254442&filetypes[]=pdf&langs[]=en'
    regex_zipfiles = 'http://aleph.gutenberg.org/.*\.zip'
    regex_nextpage = 'harvest\?offset\=\d+\&filetypes\[\]\=pdf\&langs\[\]\=en'
    
    if not os.path.isabs(directory):
        directory = os.path.abspath(directory)
    
    create_directory(directory)
    
    while url:
        
        logger.info("Requesting url: '{}'".format(url))
        
        resp = fetch_url(url, useragent_file)
        soup =  bs(resp.content, 'lxml')
        
        url = None
        links_zipfiles = []
        for link in soup.find_all('a', href=True):
            if re.search(regex_zipfiles, link['href']):
                links_zipfiles.append(link['href'])
                
            if re.search(regex_nextpage, link['href']):
                url = link['href']
                url = url if is_absolute(url) else \
                            urljoin('http://aleph.gutenberg.org/', url)
        
        
        for link_zipfile in links_zipfiles:
            resp = fetch_url(link_zipfile, useragent_file)
            zip_file = zipfile.ZipFile(io.BytesIO(resp.content))
            for file in zip_file.namelist():
                if file.endswith(extensions) and \
                    not os.path.exists(file):
                    
                    zip_file.extract(file, directory)
                    logger.info("[  url  ]  '{}'  [  file  ]  '{}'  [  saved  ]  '{}'".
                          format(link_zipfile, file, directory))
                    
            zip_file.close()
            time.sleep(time_sleep_sec)
        
        time.sleep(time_sleep_sec)
        
    sys.exit(0)