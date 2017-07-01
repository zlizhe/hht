#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import urllib
import urllib2
import re
import os
import thread
# import threading
import math
import sys
import time

class DlHhtRes():
    '''
    Version 1.x
    下载火火免APP 所有 该分类下的 mp3文件并按 类型分类存放
    使用 json 离线下载
    '''

    # 下载线程数
    _onDlNum = 50

    # 已下载文件数
    _fileNum = 0

    _taskName = {
        '1': '下载并保存文件'.decode('utf-8'),
        '2': '重新更新数据源'.decode('utf-8')
    }

    # 下载归类使用的文件夹名称
    _categoryName = {
        '1': '儿歌'.decode('utf-8'),
        '2': '故事'.decode('utf-8'),
        '3': '英语'.decode('utf-8'),
        '4': '古诗'.decode('utf-8'),
        '5': '伴眠'.decode('utf-8')
    }

    # 当前正在操作的分类所有内容页的链接地址
    _doCategoryIds = []

    # 当前正在操作的内容页的所有下载地址 对应文件名称
    _res = []

    # 获取下载链接
    def getDlUrl(self, spName):
        import requests
        r = requests.post("http://www.alilo.com.cn/gw/resource/music", data={'specialname': spName})
        #print r.text[musicList]
        listJson = json.loads(r.text)
        if listJson.has_key('content'):
            musicList = listJson['content']['musicList']
            print str(len(musicList)) + ' \'s musics' + ' in category ' + spName

            if len(musicList) > 0:
                # 所有下载链接
                for music in musicList:
                    self._res.append({
                        'res': music['path'],
                        'name': music['name']
                    })
        return



    # 获取分类链接
    def getCategoryName(self, catName):
        import requests
        r = requests.post("http://www.alilo.com.cn/gw/resource/special", data={'classname': catName, 'classid': 0})
        #print r.text[musicList]
        listJson = json.loads(r.text)
        if listJson.has_key('content'):
            specialList = listJson['content']['specialList']
            # 没有数据
            if len(specialList) > 0:
                # 所有分类写入下载链接
                for cate in specialList:
                    self.getDlUrl(cate['name'])
        return

    # 开始执行所有下载操作
    def __init__(self, ac = '1', category=''):
        if __name__ == '__main__':
            if category:
                print 'Your insert category is ' + self._categoryName[category]
            # 首先跑完所有分类以及页码 把所有 id 存储下来
            for category in [category] if category else self._categoryName:
                # 下载指令
                if '1' == ac:
                    self.openJson(category)
                    if len(self._res) > 0:
                        # 下载并命名归类文件
                        self.downloadFile(self._categoryName[category])
                        time.sleep(3)
                    print str(self._fileNum) + ' files download completed, Mission complete.'
                    # 操作完成后关机 windows 下 @todo 文件数量太大 可以使用下载完成后关机 only windows
                    # os.system('shutdown -s -t %d' % 1)

                # 保存 数据
                if '2' == ac:
                    self.getCategoryName(self._categoryName[category])
                    self.saveJson(category)
                    # 下载并命名归类文件
                    # self.downloadFile(self._categoryName[category])
                    print str(len(self._res)) + ' datas save completed in ./res/' + str(category) + '.json'
                    time.sleep(3)


    # 打开数据包
    def openJson(self, catid):
        with open('./res/' + catid + '.json', 'r') as f:
            self._res = json.load(f)
        return

    # 存 json
    def saveJson(self, catid):
        # 创建文件夹
        if False == os.path.isdir('res'):
            os.mkdir('res')

        if len(self._res) > 0:
            # 写本分类所有内容至 ./res/catid.json 文件
            with open('./res/' + catid + '.json', 'w') as f:
                f.write(json.dumps(self._res))
        return

    # 存储所有信息
    def saveData(self, category):
        import pymysql.cursors
        import pymysql
        # Connect to the database
        connection = pymysql.connect(host='localhost',
                                     user='root',
                                     password='',
                                     db='hht',
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)

        try:

            #  当前分类
            with connection.cursor() as cursor:
                # Read a single record
                sql = "SELECT `id`, `typename`, `py` FROM `type` WHERE `py` = %s"
                cursor.execute(sql, category)
                typeArr = cursor.fetchone()


            # 写入本分类下所有内容
            with connection.cursor() as cursor:
                for resOne in self._res:
                    sql = "INSERT INTO `res` (`type_id`, `name`, `link`) VALUES (%s, %s, %s)"
                    cursor.execute(sql, (typeArr['id'], resOne['name'], resOne['res']))

            connection.commit()
            print 'Insert ' + str(len(self._res)) + ' datas with category ' + typeArr['typename']
            del typeArr


        finally:
            connection.close()
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
taskType = None
def waitUserCate():
    global userCate
    msg = u'请输入分类 序号 开始下载或直接回车下载所有分类文件：'
    userCate = raw_input(msg.encode(sys.stdin.encoding)).decode(sys.stdin.encoding)

def waitUserTask():
    global  taskType
    msg = u'请输入任务类型序号 ：'
    taskType = raw_input(msg.encode(sys.stdin.encoding)).decode(sys.stdin.encoding)

print u'::1:: 这里是所有可用分类 ID 以及其对应名称: '
for (py, cName) in DlHhtRes._categoryName.items():
    print py + ' : ' + cName
while userCate not in DlHhtRes._categoryName and userCate != '':
    waitUserCate()
    pass
else:
    print u'::2:: 这里是可用的任务类型, 为防止火火兔再次更新接口导致下载器不可用, 目前这一版本已自带数据源一般用户无需 重新更新数据源 直接选择下载并保存文件即可, 如需更新数据源, 请备份 ./res/ 文件夹后 确认已安装 requests (pip install requests) 后执行 重新更新数据源 操作之后再次执行 下载并保存文件 即可'
    for (py, name) in DlHhtRes._taskName.items():
        print py + ' : ' + name

    while taskType not in DlHhtRes._taskName:
        waitUserTask()
        pass
    else:
        DlHhtRes(taskType, userCate)
