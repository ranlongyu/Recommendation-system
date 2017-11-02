import re
import json
import jieba.analyse
import os
from sklearn.cluster import KMeans
from sklearn import preprocessing

#获取原始数据
def get_lines():
    #lines为列表，里面是每一行的字典
    filename = "user_click_data.txt"
    with open(filename, encoding='UTF-8') as file:
        lines = []
        for line in file:
            line_division = re.match(r'(.*)\t(.*)\t(.*)\t(.*)\t(.*)\t(.*)', line)
            line_dic = {
                'user_id': line_division.group(1),
                'news_id': line_division.group(2),
                'view_time': line_division.group(3),
                'news_title': line_division.group(4),
                'news_contents': line_division.group(5),
                'news_time': line_division.group(6),
            }
            lines.append(line_dic)
        return lines
#获取所以新闻列表
def get_all_news(lines):
    all_news = []
    for line in lines:
        news = {
            'news_title': line['news_title'],
            'news_contents': line['news_contents'],
            'news_time': line['news_time'],
        }
        all_news.append(news)
    #去除重复项
    seen = set()
    new_all_news = []
    for d in all_news:
        t = tuple(d.items())
        if t not in seen:
            seen.add(t)
            new_all_news.append(d)
    #写入文件
    filename = 'all_news.json'
    with open(filename, 'w') as f_obj:
            json.dump(new_all_news, f_obj)
#构建词典
def get_keywords():
    filename = 'all_news.json'
    keywords = []
    with open(filename) as f_obj:
        all_news = json.load(f_obj)
        all_contents = ''
        for news in all_news:
            all_contents = all_contents + news['news_contents']
        for word in jieba.analyse.textrank(all_contents, topK=3000):
            keywords.append(word)
    return keywords
#构建文本向量
def get_all_text_vectors(keywords):
    all_text_vectors = []
    filename = 'all_news.json'
    with open(filename) as f_obj:
        all_news = json.load(f_obj)
        for news in all_news:
            text_vectors = []
            for word in keywords:
                text_vectors.append(news['news_contents'].count(word))
            all_text_vectors.append(text_vectors)
    return all_text_vectors
#构建分类器
def get_km_cluster():
    all_text_vectors = get_all_text_vectors(get_keywords())
    clf = KMeans(n_clusters=10, max_iter=3000)
    #归一化后，进行聚类
    all_text_vectors = preprocessing.normalize(all_text_vectors, norm='l2')
    clf.fit(all_text_vectors)
    #将新闻类别写入文件
    filename = 'all_news.json'
    with open(filename, 'r+') as f_obj:
        new_all_news = []
        all_news = json.load(f_obj)
        for i, news in enumerate(all_news):
            news['news_type'] = str(clf.labels_[i])
            new_all_news.append(news)
    #删除以前的文件
    if os.path.exists(filename):
        os.remove(filename)
    filename = 'all_news.json'
    with open(filename, 'w') as f_obj:
        json.dump(new_all_news, f_obj)
#新闻推荐
def recommend():
    lines = get_lines()
    while True:
        print('=' * 40)
        user_id = input("请输入用户编号或输入shutdown结束：")
        if user_id == 'shutdown':
            break
        print('=' * 40)
        print("该用户阅读了下列新闻：")
        print('=' * 40)
        view_news = []
        for line in lines:
            if line['user_id'] == user_id and line['news_title'] not in view_news:
                print(line['news_title'])
                view_news.append(line['news_title'])
        filename = 'all_news.json'
        recommend_news = []
        with open(filename) as f_obj:
            all_news = json.load(f_obj)
            news_type = ''
            for news_title in view_news:
                for news in all_news:
                    if news_title == news['news_title']:
                        news_type = news['news_type']
                        break
                for news in all_news:
                    if news_type == news['news_type'] and news['news_title'] not in view_news:
                            recommend_news.append(news)
            #按照时间最近排序
            #recommend_news = sorted(recommend_news, key=lambda k: k['news_time'], reverse=True)
            print('=' * 40)
            print("推荐的新闻如下：")
            print('=' * 40)
            for i, news in enumerate(recommend_news):
                print(news['news_title'], news['news_time'])
                if i > 10:
                    break

#get_all_news(get_lines())
#get_km_cluster()
recommend()