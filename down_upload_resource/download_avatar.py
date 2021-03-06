#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from handle_mysql import MySQL
import json
from urllib.parse import urlparse
import requests
import os
from down_upload_resource.upload_file import upload_file
from down_upload_resource.delete_dir import clear_dir
import time
import pickle

'下载资源'

proxies={
    'https':'https://112.87.71.153:9999'
}
audio_headers = {
    'Accept': 'application/json,application/xml,application/xhtml+xml,text/html;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh',
    'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
    'User-Agent': 'Mozilla/5.0 (Linux; U; Android 7.1.2; zh-cn; ALP-AL00 Build/HUAWEIALP-AL00) AppleWebKit/533.1 (KHTML, like Gecko) Version/5.0 Mobile Safari/533.1'
}

image_headers = {
    'Accept':'image/webp,image/*,*/*;q=0.8',
    'Accept-Encoding':'gzip, deflate',
    'Accept-Language':'zh-CN,en-US;q=0.8',
    'User-Agent':'okhttp/3.11.0'

}
def down_dedao():
    global problem_list
    mysql = MySQL()

    try:
        mysql.get_connection()

        select_results = mysql.select('article',['article_id','article_content'],'avatar_uploaded = 0')

        print(len(select_results))
        problem_list = []
        # type:"audio , audio:"
        # type:"image , src:"
        for result in select_results:
            resource_list = []
            # 文章id
            id = result[0]

            # 追加作者头像信息
            article_author = mysql.select('article_author', ['article_id', 'author_id'],
                         'article_id = ' + str(id))
            author_info = mysql.select('author',['author_name','author_avatar'], 'author_id = ' + str(article_author[0][1]))
            resource_list.append(author_info[0][1])


            # 查封面
            ext_attributes = mysql.select('ext_attribute',['article_id','attribute_name','attribute_value'],'article_id = ' + str(id))
            for ext_attribute in ext_attributes:
                # 评论头像追加
                if ext_attribute[1] == 'comment':
                    comment = json.loads(ext_attribute[2])
                    for note in comment['list']:
                        resource_list.append(note['notes_owner']['avatar'])


            # 文章正文
            try:

                # 先创建目录
                os.mkdir(os.path.join(os.path.abspath('resource'), str(id)))
                # resource_path_list = []
                # 对当前文章的链接一个一个进行下载,构造请求头（分析一下）
                for resource in resource_list:
                    # 下载音频
                    # if '.m4a' in resource or '.mp4' in resource:
                    audio_parse = urlparse(resource)
                    if '.m4a' in resource or '.mp4' in resource:
                        audio_headers['Host'] = audio_parse[1]
                        audio = requests.get(resource, headers=audio_headers)
                    else:
                        image_headers['Host'] = audio_parse[1]
                        audio = requests.get(resource, headers=image_headers)

                    # 解析出资源名
                    audio_name = audio_parse[2][audio_parse[2].rfind('/') + 1:]
                    # 把文章资源放到resource/id/...
                    with open(os.path.join(os.path.abspath('resource'), str(id), audio_name), 'wb') as f:
                        f.write(audio.content)
                    print('资源下载成功：%s' % os.path.join(os.path.abspath('resource'), audio_name))
                    time.sleep(2)

            except:
                problem_list.append(id)


    finally:
        print(problem_list)
        mysql.close_connection()


if __name__ == '__main__':
    down_dedao()