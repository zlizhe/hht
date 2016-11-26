#!/usr/bin/env python
# -*- coding=utf-8 -*-
import urllib
import urllib2
import re
import os
import thread
#import threading
import math
import sys
import time

class DlHhtRes():
    '''
    下载火火免官网 所有 该分类下的 mp3文件并按 类型分类存放
    http://www.alilo.com.cn/?app=music&action=list&cid=gushichengbao&age=0&order=hot
    '''

    # 下载线程数
    _onDlNum = 200

    # 已下载文件数
    _fileNum = 0

    # 所有需要下载的分类
    _category = ['gushichengbao', 'ertongyinyue', 'xiguanxingge', 'guoxuetang']

    # 下载归类使用的文件夹名称
    _categoryName = {
        'gushichengbao': '故事'.decode('utf-8'),
        'ertongyinyue': '儿歌'.decode('utf-8'),
        'guoxuetang': '科普知识'.decode('utf-8'),
        'xiguanxingge': '习惯性格'.decode('utf-8')
    }

    # 当前正在操作的分类所有内容页的链接地址
    _doCategoryIds = []

    # 当前正在操作的内容页的所有下载地址 对应文件名称
    _res = []

    # 开始执行所有下载操作
    def __init__(self, category=''):
        if __name__ == '__main__':
            if category:
                print 'Your insert category is ' + self._categoryName[category]
            # 首先跑完所有分类以及页码 把所有 id 存储下来
            for category in [category] if category else self._category:
                self.getCategoryList(category)

                if not self._doCategoryIds:
                    print self._categoryName[category] + '\'s Detail ids is empty.'
                    continue

                # 通过 id 抓取所有 detail 页面的 mp3 地址
                self.getDetailList()

                if not self._res:
                    print self._categoryName[category] + '\'s Res ids is empty.'
                    continue

                # 下载并命名归类文件
                self.downloadFile(self._categoryName[category])
                time.sleep(3)

            print str(self._fileNum) + ' files download completed, Mission complete.'
            # 操作完成后关机 windows 下 @todo 文件数量太大 可以使用下载完成后关机
            # os.system('shutdown -s -t %d' % 1)


    # 取该分类的 所有内容页链接和标题
    def getCategoryList(self, category):

        # 分类中所有的 li
        def findCategoryLi(html):
            # 截取正文段
            start = html.index('<ul class="gseg_list_left_ul">')
            try:
                end = html.index('<div class="pages_content">')
            except:
                # 无分页的页面
                end = html.index('<div class="gseg_list_right">')

            # print end
            # exit()
            # 正文所有需要内容
            mainContent = html[start:end]

            # print mainContent

            # 正则取所有 li list
            # parttern = re.compile(r"<li.*?\/li>")
            mainContent = re.compile('\n|\r').sub('', mainContent)  # 去除所有 \n
            # print mainContent
            return re.findall(r"<li>(.*?)</li>", mainContent)

        def findCategoryId(liList):
            # 从所有 li 中 找到 id
            for li in liList:
                startString = 'http://www.alilo.com.cn/?app=music&action=detail&id='
                start = li.index(startString)
                end = li.index('" target="_blank">')
                newId = li[start + len(startString):end]

                # 已存在的 id
                if newId not in self._doCategoryIds:
                    self._doCategoryIds.append(newId)
            return

        page = 0
        # 没有资源时跳出页码
        while True:
            page += 1
            response = urllib2.urlopen('http://www.alilo.com.cn/?app=music&action=list&cid=' + category + '&age=0&order=hot&page=' + str(page))
            html = response.read().lower()

            # all li html in list
            liList = findCategoryLi(html)
            # print liList
            # exit()

            # 没有任何内容的 category 或 page is max
            if not liList:
                print '[Empty] ' + self._categoryName[category] + ' in page ' + str(page) + ' do not have content, its over.'
                break
            else:
                print self._categoryName[category] + ' in page ' + str(page) + ' was ready.'

            # all id in list
            findCategoryId(liList)
            # print len(liList)
            # print self._doCategoryIds
            # print len(self._doCategoryIds)
            # # print re.findall(parttern, mainContent)
            # exit()


    # 取详细内容页所有可下载的链接地址
    def getDetailList(self):

        # 内容中所有的 li
        def findDetailLi(html):
            # 截取正文段
            start = html.index('<div class="gseg_dvd_play_list_m">')
            end = html.index('<a href="#" id="check_this_all"></a>')

            # 正文所有需要内容
            mainContent = html[start:end]

            # 正则取所有 li list
            # parttern = re.compile(r"<li.*?\/li>")
            mainContent = re.compile('\n|\r').sub('', mainContent)  # 去除所有 \n
            # print mainContent
            return re.findall(r"<li (.*?)</li>", mainContent)

        # 从 liList 中找到可供下载使用 Res
        def findResData(liList):

            #get Res
            def getRes(data):
                startString = 'ref="'
                start = data.index(startString)
                end = data.index('" name=')
                return data[start + len(startString):end].strip()

            # res's name
            def getName(data):
                startString = 'title=" '
                start = data.index(startString)
                end = data.index('" cover=')

                return data[start + len(startString):end].strip()

            for li in liList:

                # format name and res in dict
                resData = {
                    'res': getRes(li),
                    'name': getName(li).decode('utf-8')
                }

                if resData not in self._res:
                    self._res.append(resData)
                #     print resData['name'] + ' ' + resData['res'] + ' is in it.'

            # print self._res
            # print len(self._res)
            # exit()
            return

        for id in self._doCategoryIds:
            response = urllib2.urlopen('http://www.alilo.com.cn/?app=music&action=detail&id=' + id)
            html = response.read()

            # 所有 liList
            liList = findDetailLi(html)

            if not liList:
                print '[Empty] Detail page ' + id + ' can not find res.'
                continue

            # 查找所有 Res
            findResData(liList)

        # 清空 详情内容队列
        del self._doCategoryIds[:]
        return


    # 线程状态
    _threadsStatus = {}
    # 下载该文件
    def downloadFile(self, categoryName):
        # 创建文件夹
        if False == os.path.isdir(categoryName):
            os.mkdir(categoryName)


        # 所有线程下载总数
        self.allThreadNum = 0
        def dl(threadName, delay, res):

            # 取文件扩展名称
            def getFileExp(file):
                return '.'+file[-3:]

            # 当前所有线程总下载数
            self.allThreadNum += 1
            # 下载文件 至分类目录 并重新命名
            fileName = categoryName + '/' + res['name'] + getFileExp(res['res'])

            if not os.path.isfile(fileName):
                urllib.urlretrieve(res['res'], fileName)
                # 已下载的总文件数量
                self._fileNum += 1
                print threadName + res['name'] + ' file ' + res['res'] + ' is download.'
            else:
                print threadName + res['name'] + ' file ' + res['res'] + ' is exist.'
            # 释放线程占用
            del self._threadsStatus[threadName]
            thread.exit_thread()
            time.sleep(2)

        # 下载总数
        dlNum = len(self._res)
        try:
            # threadNum = int(math.ceil(dlNum / float(self._onDlNum)))
            # 5线程下载
            # 还剩下多少 需要开启多少线程
            # lastedNum = dlNum % self._onDlNum
            threadNum = dlNum if dlNum < self._onDlNum else self._onDlNum
            print categoryName + ' was download by ' + str(threadNum) + ' threads with ' + str(dlNum) + ' files.'
            # 所有资源
            for dlres in self._res:
                # 所有线程
                for i in xrange(self._onDlNum):
                    # 如果当前线程空闲则给他操作，否则什么也不做
                    threadI = 'Thread-' + str(i)
                    if not self._threadsStatus.has_key(threadI):
                        # 开启新线程
                        self._threadsStatus[threadI] = dlres
                        thread.start_new_thread(dl, (threadI, i + 2, dlres))
                        # 跳出线程 走下一个资源
                        break
                    else:
                        # 当前线程忙 
                        continue
                    # 开始项目
                    #startRes = (dlNum // self._onDlNum) * i
                    # 结束项目
                    #endRes = (startRes + startRes) if i >= threadNum else None
                    #thread.start_new_thread(dl, ('[Thread-' + str(i) + '] ', i + 2, self._res[startRes : endRes]))
                # 检查是否有空闲线程
                while len(self._threadsStatus) >= self._onDlNum:
                    pass
        except:
            print 'Download thread start error' , sys.exc_info()[0]
            raise

        # # 所有线程中还有未下载完成的
        # while self.allThreadNum < dlNum:
        #     pass

        print categoryName + str(len(self._res)) + ' files download completed.'
        # 清空本category 使用的下载队列
        del self._res[:]
        return

userCate = None
def waitUserCate():
    global userCate
    userCate = raw_input(u'请输入正确分类拼音开始下载或直接回车下载所有分类文件：'.encode('gbk'))

print u'这里是所有可用分类拼音及其对应名称: '
for (py, cName) in DlHhtRes._categoryName.items():
    print cName + ' : ' + py
while userCate not in DlHhtRes._category and userCate != '':
    waitUserCate()
    pass
else:
    DlHhtRes(userCate)
