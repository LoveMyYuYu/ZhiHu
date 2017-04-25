# -*- coding:utf-8 -*-

import sys
sys.path.append("H://relax")

import requests
import cookielib
import re
import time
import os
import codecs
import csv

try:
    from PIL import Image
except:
    pass
from users import get_user

    
# 构造 Request headers
# agent = 'Mozilla/5.0 (Windows NT 5.1; rv:33.0) Gecko/20100101 Firefox/33.0'
agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586"
headers = {
    "Host": "www.zhihu.com",
    "Referer": "https://www.zhihu.com/",
    'User-Agent': agent
}

class Zhihu(object):
    
    PATH = os.path.dirname(os.path.abspath(__file__))
    session = requests.Session()
    FILENAME = "user_infos.csv"
    TESTED_FILENAME = "tested_links.txt"
    
    def __init__(self):
        self.session.cookies = cookielib.LWPCookieJar(filename=self.PATH+'/cookie')
        self.user_links = []
        self.tested_links = []
        self.get_tested_links()
        try:
            f = open(self.PATH + "/" + self.FILENAME,"r")
            f.close()
        except:
            try:
                f = open(self.PATH + "/" + self.FILENAME,"w")
                f.write(codecs.BOM_UTF8)
                s = csv.writer(f)
                s.writerow( [ "用户名","签名", "关注人数", "粉丝数", "分享数", "回答数",
                              "提问数", "收藏数", "链接" ] )
                f.close()
            except Exception, e:
                print e.message
                print u"init failed,exit.."
                exit()
    
    def get_html(self,url):
        try:
            res = self.session.get(url,headers=headers)
            if res.status_code == 200:
                return res.text
            else:
                return None
                
        except requests.exceptions.ConnectTimeout:
            print u"timeout"
            return None
            
        except requests.exceptions.ConnectionError:
            print u"请检查你的网络连接..."
            flag = False
            while not flag:
                try:
                    t = requests.get("http://www.baidu.com",timeout=2)
                    if t.status_code == 200:
                        flag = True
                except:
                    time.sleep(10)
                # 如果没网，则10秒判断一次是否联网
            print u"已联网"
            self.get_html(url)
            
        except Exception,e:
            print e.message
            print u"unknow error in request %s"%url
            return None
        
    # 获取验证码
    def get_captcha(self):
        t = str(int(time.time() * 1000))
        captcha_url = 'https://www.zhihu.com/captcha.gif?r=' + t + "&type=login"
        r = self.session.get(captcha_url, headers=headers)
        with open(self.PATH + '/captcha.jpg', 'wb') as f:
            f.write(r.content)
            f.close()
        # 用pillow 的 Image 显示验证码
        # 如果没有安装 pillow 到源代码所在的目录去找到验证码然后手动输入
        try:
            im = Image.open('captcha.jpg')
            im.show()
            im.close()
        except:
            print(u'请到 %s 目录找到captcha.jpg 手动输入' % (self.PATH + '/captcha.jpg'))
        captcha = raw_input("please input the captcha\n>")
        return captcha  
    
    # 从本地获取已经爬过的用户
    def get_tested_links(self):
        try:
            f = open(self.PATH + "/" + self.TESTED_FILENAME,"r")
            content = f.read().decode("utf-8")
            self.tested_links = content.split("\n")
            f.close()
            print u"get tested links success!"
        except Exception, e:
            print e.message
            print "local has no tested links yet."
    
    # 保存已经爬过的用户链接
    def save_tested_links(self,user):
        try:
            f = open(self.PATH + "/" + self.TESTED_FILENAME,"a")
            f.write(user.encode("utf-8") + "\n")
            f.close()
        except Exception,e:
            print e.message
            print u"保存 %s到本地以抓取文件失败"%user
            
    def login(self,username,password):
        if self.isLogin():
            print "login success with exist cookies!"
            return
            
        post_url = 'https://www.zhihu.com/login/phone_num'
        login_html = self.session.get("https://www.zhihu.com",headers=headers).text
        _xsrf = re.search('name="_xsrf" value="(.*?)"',login_html).group(1)
        print _xsrf
        postdata = {
            '_xsrf': _xsrf,
            'password': password,
            'remember_me': 'true',
            'phone_num': username,
        }
        try:
            # 不需要验证码直接登录成功
            login_page = session.post(post_url, data=postdata, headers=headers)
            login_code = login_page.json()
            print login_page.text
            print(login_page.status_code)
            print(login_code['msg'])
        except:
            # 需要输入验证码后才能登录成功
            postdata["captcha"] = self.get_captcha()
            login_page = self.session.post(post_url, data=postdata, headers=headers)
            #print login_page.text
            #login_code = login_page.json()
            #print(login_code['msg'])
            h = session.get("https://www.zhihu.com")
            print h.text
        self.session.cookies.save()
        
    def isLogin(self):
        try:
            self.session.cookies.load(ignore_discard=True)
        except:
            print(u"Cookie 未能加载")
        url = "https://www.zhihu.com/settings/profile"
        #url = "https://www.zhihu.com/"
        login_code = self.session.get(url, headers=headers, allow_redirects=False)
        if login_code.status_code == 200:
            # print session.cookies
            #print login_code.text
            return True
        else:
            return False
      
    # 因为并不需要获取用户的具体关注者，所以不需要处理翻页问题
    # 获取用户的关注者链接，所有用户连接的来源
    def get_user_followings(self,user):
        url = 'http://www.zhihu.com' + user + "/following"
        user_page = self.get_html(url)
        if not user_page:
            print u"get html error in %s"%url
            return 
        followings = re.findall('<a class="UserLink-link".*?href="(.*?)"',user_page,re.S)
        for i in followings:
            if i in self.tested_links:
                # print u'%s exists'%i
                continue
            self.tested_links.append(i)
            self.user_links.append(i)
    
    # 获取用户信息
    def get_user_info(self,user):
        '''
        保存的格式{
                    "id" : id,
                    "url" : url,
                    "sign" : sign,(签名，行业信息不容易捕捉)
                    "follows" : follows,
                    "followings" : followings,
                    "shares" : shares,
                    "answers" : answers,
                    "questions" : questions,
                    "collections" : collections
                    }
        '''
        url = "https://www.zhihu.com" + user + "/answers"
        user_page = self.get_html(url)
        if not user_page:
            print u"get html error in %s"%url
            return None
        info = {}
        attrs = [ "id", "url", "sign","followings", "follows", 
                  "shares", "answers", "questions", "collections" ]
        for attr in attrs:
            info[attr] = ""
        
        info["url"] = url
        id = re.search('<span class="ProfileHeader-name">(.*?)</span>',user_page,re.S)
        if id:
            info["id"] = id.group(1)
            print u"正在获取 %s 的信息"%id.group(1)
        else:
            print u"没有获取到 %s 的信息"%url
            return None
        sign = re.search('<span class="RichText ProfileHeader-headline">(.*?)</span>',user_page,re.S)
        if sign:
            info["sign"] = sign.group(1)
        follow = re.findall('<div class="NumberBoard-value">(.*?)</div>',user_page,re.S)
        if follow:
            if len(follow) == 2:
                info["followings"] = follow[0]
                info["follows"] = follow[1]
        others = re.findall('<span class="Tabs-meta">(.*?)</span>',user_page,re.S)
        if others:
            if len(others) == 4:
                info["answers"] = others[0]
                info["shares"] = others[1]
                info["questions"] = others[2]
                info["collections"] = others[3]
        return info    
        
    def save_user_info(self,info):
        try:
            f = open(self.PATH + "/" + self.FILENAME,"ab")
            f.write(codecs.BOM_UTF8)
            s = csv.writer(f)
            for i in info.keys():
                try:
                    info[i] = info[i].encode("utf-8")
                except:
                    pass
            s.writerow(
                        [ info["id"],info["sign"],info["followings"],info["follows"],\
                          info["shares"],info["answers"],info["questions"],info["collections"],info["url"]]
                    )
            f.close()
        
        except Exception, e:
            print e.message
            print u"保存%s的信息失败"%info["id"].decode("utf-8")
        
    def get_followings(self):
        user_number = 0
        for user in self.user_links:
            user_followings = self.get_user_followings(user)
            time.sleep(1)
            info = self.get_user_info(user)
            if not info:
                continue
            self.save_user_info(info)
            self.save_tested_links(user)
            user_number += 1
            print u"grap numbers yet  : %d"%user_number
            # 防止速度过快，被服务器封掉
            time.sleep(1)
        print u"哇。终于爬完了！"
        print u"一共为您获取到了%d为用户的信息！"%user_number

    def run(self):
        start_time = time.time()
        pwd = get_user("zh")
        self.login("18895379450",pwd)
        # 从我的主页开始爬取
        self.user_links.append("/people/bi-zhong-liang-33")
        self.get_followings()
        time_used = time.time() - start_time
        print u"一共用时%s秒"%time_used
      
if __name__ == "__main__":
    Zhihu().run()


    