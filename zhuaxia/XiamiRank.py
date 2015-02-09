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

#=====================================
song_hot_floor = 90000
singerNum = 170
myArtistList = []
with open('韩国乐队', 'r') as f:
    myArtistList = f.read().splitlines()
#=====================================


# LOG = log.get_logger("zxLogger")

dl_songs = []
total = 0
done = 0

fmt_parsing = u'解析: "%s" ..... [%s] %s' 
fmt_has_song_nm = u'包含%d首歌曲.' 
fmt_single_song = u'[曲目] %s'
border = log.hl(u'%s'% ('='*90), 'cyan')

pat_xm = r'^https?://[^/.]*\.xiami\.com/'
pat_163 = r'^https?://music\.163\.com/'

#proxypool
ppool = None

def shall_I_begin(url, is_file=False, is_hq=False, need_proxy_pool = False):
    #start terminate_watcher
    # Terminate_Watcher()
    global ppool
    if need_proxy_pool:
        print '初始化proxy pool'
        ppool = ProxyPool()
        print('proxy pool:[%d] 初始完毕'%len(ppool.proxies))

    #xiami obj
    xiami_obj = xm.Xiami(config.XIAMI_LOGIN_EMAIL,\
            config.XIAMI_LOGIN_PASSWORD, \
            is_hq,proxies=ppool)
    #netease obj
    m163 = netease.Netease(is_hq, proxies=ppool)

    #用来得到歌手ID的排序名单txt，用过一次就行了，什么时候想起来了再更新一次
    # artistIDs = getTopArtists(xiami_obj, url)

    getTopSongs(xiami_obj)

def getTopSongs(xm_obj):

    songIDList = []
    songTitleList = []
    songHotList = []
    artistNameList = []

    for i in xrange(0,len(myArtistList)):
        print "Get to the " + str(i) + "th "+"singer"
        artistID = myArtistList[i]

        if i > singerNum:
            break

        htmlFile = getHtmlFile(artistID, xm_obj, 1)

        if appendSong(htmlFile, songIDList, songTitleList, songHotList, artistNameList) != 20:
            continue

        currentPage = 2
        while True:
            htmlFile = getHtmlFile(artistID, xm_obj, currentPage)

            if  appendSong(htmlFile, songIDList, songTitleList, songHotList, artistNameList) == 20 \
             and currentPage <= 4:
                currentPage += 1
                continue
            else:
                break

    numOfSongs = len(songIDList)
    multiDimenList = []
    for i in xrange(0, numOfSongs):
        newSong = []
        newSong.append(songIDList[i])
        newSong.append(songTitleList[i])
        newSong.append(songHotList[i])
        newSong.append(artistNameList[i])
        multiDimenList.append(newSong)

    sortedSongList = sorted(multiDimenList,key=lambda x: x[2], reverse = True)

    fileName = 'songRank.html'
    f=file(fileName,'w')
    f.write('<!DOCTYPE html>\n<html>\n<head>\n')
    f.write('<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">\n')
    f.write('</head>\n\n<body>\n')
    f.write('<h1>虾米音乐榜单</h1>'+' '+'<h3>第一版</h3>')  #标题

    count = 0
    for i in xrange(0,numOfSongs):
        link = "http://www.xiami.com/song/"+str(sortedSongList[i][0])
        title = sortedSongList[i][1]
        hot = sortedSongList[i][2]
        singer = sortedSongList[i][3]
        f.write('<p>'+str(count)+'. '+'歌手: '+str(singer)+
            '<a href=\"'+str(link)+'\">'+str(title)+'</a>'+' 试听人数：'+str(hot)+'\n')
        count += 1

    f.write('</body>')
    f.close()

    webbrowser.open('file://' + os.path.realpath(fileName))


def getHtmlFile(artistID, xm_obj, pageNum):
    filePath = './HtmlFile/'+artistID+'-'+str(pageNum)+'.html'
    if path.isfile(filePath):
        with open(filePath, 'r') as savedHtml:
            htmlFile = savedHtml.read() 
            return htmlFile
    else:
        # print "downloading "+artistID+"'s "+str(pageNum)+" page"
        if pageNum == 1:
            url = "http://www.xiami.com/artist/top-" + artistID
            htmlFile = xm_obj.read_link(url).content
            htmlFileLocal = open(filePath,'w')
            htmlFileLocal.write(htmlFile)
            htmlFileLocal.close()
        else:
            url = "http://www.xiami.com/artist/top-" + artistID
            url += "?&page="+str(pageNum)
            htmlFile = xm_obj.read_link(url).content
            htmlFileLocal = open(filePath,'w')
            htmlFileLocal.write(htmlFile)
            htmlFileLocal.close()

        return htmlFile

def appendSong(htmlFile, songIDList, songTitleList, songHotList, artistNameList):
    soup = BeautifulSoup(htmlFile)
    song_ids = re.findall(r'/song/(.+?)" title', htmlFile)
    song_titles = re.findall(r'/song/(0|1|2|3|4|5|6|7|8|9)+" title="(.+?)"', htmlFile)
    song_hot = re.findall(r'class="song_hot">(.+?)<', htmlFile)
    artistName = re.findall(r'/artist/(0|1|2|3|4|5|6|7|8|9)+">(.+?)<span>', htmlFile)

    count = 0
    for i in xrange(0,len(song_ids)):
        if int(song_hot[i]) > song_hot_floor:
            count += 1
            songIDList.append(str(song_ids[i]))
            songTitleList.append(str(song_titles[i][1]))
            songHotList.append(int(song_hot[i]))
            artistNameList.append(str(artistName[0][1]))
        else:
            break

    return count


#我加的，返回一个list的最佳歌手
def getTopArtists(xm_obj, url):
    myArtistTxt = open('ArtistTxt', 'w')

    artistList = []
    fanNumList = []
    artistIDList = []
    htmlFile = xm_obj.read_link(url).content
    appendArtist(htmlFile, artistList, fanNumList, artistIDList)

    currentPage = 2
    while True:
        print "Current page is " + str(currentPage)
        url += "/page/"+str(currentPage)
        htmlFile = xm_obj.read_link(url).content
        if appendArtist(htmlFile, artistList, fanNumList, artistIDList) == 24:
            currentPage += 1
            continue
        else:
            break

    numOfArtists = len(artistList)
    multiDimenList = []
    for i in xrange(0, numOfArtists):
        newArtist = []
        newArtist.append(artistList[i])
        newArtist.append(fanNumList[i])
        newArtist.append(artistIDList[i])
        multiDimenList.append(newArtist)

    sortedArtistList = sorted(multiDimenList,key=lambda x: x[1], reverse = True)

    longArtistIDString = ""
    for i in xrange(0,numOfArtists):
      longArtistIDString += str(sortedArtistList[i][2])
      longArtistIDString += "\n"

    myArtistTxt.write(longArtistIDString)
    myArtistTxt.close()


def appendArtist(htmlFile, artistList, fanNumList, artistIDList):
    soup = BeautifulSoup(htmlFile)
    count = 0
    for link in soup.find_all("a"):
        strLink = str(link)
        if "title" in strLink and "artist" in strLink:
            count += 1
            artistName = link.get('title').encode("utf-8")
            artistStr = str(artistName)
            artistList.append(artistStr)

            href = link.get('href')
            artistID = re.findall(r'\d+',href)[0]
            artistIDList.append(int(artistID)) 

    for link in soup.find_all("p"):
        strLink = str(link)
        if "粉丝" in strLink:
            fansNum = re.findall(r'\d+',strLink)[0]
            fanNumList.append(int(fansNum))
    return count

def Main():
	shall_I_begin("http://www.xiami.com/artist/top-135", \
		is_file=False, is_hq=False, need_proxy_pool = True)
Main()
