# -*- coding:utf-8 -*-

import sys
import config ,util ,logging ,log
# import downloader
import xiami as xm
import netease
import re
from threadpool import ThreadPool
from time import sleep
from os import path
# from threadpool import Terminate_Watcher
from proxypool import ProxyPool
import urllib2
import os
from HTMLParser import HTMLParser
from bs4 import BeautifulSoup
import webbrowser

pathLoc = './HtmlFile/23975-1.html'
if path.isfile('./HtmlFile/23975.html'):
	print "yeah"

with open(pathLoc, 'r') as savedHtml:
    HtmlFile = savedHtml.read() 
    print HtmlFile