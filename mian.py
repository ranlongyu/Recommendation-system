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
def make_all_news():
    lines = get_lines()
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
#构建用户新闻向量
def make_user_news_vectors():
    lines = get_lines()
    filename = 'all_news.json'
    with open(filename) as f_obj:
        all_news = json.load(f_obj)
    user_news_vectors = {}
    for line in lines:
        if line['user_id'] not in user_news_vectors:
            user = []
            for news in all_news:
                if line['news_title'] == news['news_title']:
                    user.append(1)
                else:
                    user.append(0)
            user_news_vectors[line['user_id']] = user
        else:
            for i, news in enumerate(all_news):
                if line['news_title'] == news['news_title']:
                    user_news_vectors[line['user_id']][i] = 1
                    break
    # 写入文件
    filename = 'user_news_vectors.json'
    with open(filename, 'w') as f_obj:
        json.dump(user_news_vectors, f_obj)
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
def make_km_cluster():
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
#基于内容的新闻推荐系统
def content_recommend():
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
#基于用户的新闻推荐系统
def user_recommend():
    filename = 'user_news_vectors.json'
    with open(filename) as f_obj:
        user_news_vectors = json.load(f_obj)
    filename = 'all_news.json'
    with open(filename) as f_obj:
        all_news = json.load(f_obj)
    while True:
        user_id = input("请输入用户编号：")
        if user_id not in user_news_vectors:
            print("用户非原有用户，请从新输入")
            continue
        else:
            user = user_news_vectors[user_id]
            #找用户读过的文章，存在reading中
            readings = []
            for i, r_or_n in enumerate(user):
                if r_or_n == 1:
                    readings.append(i)
            #找读过输入用户读过文章的用户,至少三篇相同
            other_user_id = []
            for uid, other in user_news_vectors.items():
                if uid == user_id:
                    continue
                i = 0
                for reading in readings:
                    if other[reading] == 1:
                        i = i+1
                    if i == 3:
                        other_user_id.append(uid)
                        break
            #计算用户相似度,用Jaccard算法
            user_similarity = {}
            for uid in other_user_id:
                intersection = 0
                union = 0
                for (i1, i2) in zip(user, user_news_vectors[uid]):
                    if i1 == i2 == 1:
                        intersection += 1
                    if i1 == 1 or i2 == 1:
                        union += 1
                user_similarity[uid] = intersection/union
            #按用户相似度排序,返回二元组的列表
            user_similarity = sorted(user_similarity.items(), key=lambda item: item[1], reverse=True)
            #用户阅读过的新闻
            user_read = []
            for i, i1 in enumerate(user):
                if i1 ==1:
                    user_read.append(i)
            #输出新闻
            print('=' * 40)
            print('用户阅读过的新闻为：')
            print('=' * 40)
            for i, news in enumerate(all_news):
                for news_id in user_read:
                    if i == news_id:
                        print(news['news_title'])
            #进行新闻推荐
            recommend_news = []
            for user_id in user_similarity:
                for i, (i1, i2) in enumerate(zip(user, user_news_vectors[user_id[0]])):
                    if i1 == 0 and i2 == 1:
                        if i not in recommend_news:
                            recommend_news.append(i)
                            if len(recommend_news) > 20:
                                break
                if len(recommend_news) > 20:
                    break
            #输出新闻
            print('=' * 40)
            print('推荐的新闻为：')
            print('=' * 40)
            for i, news in enumerate(all_news):
                for news_id in recommend_news:
                    if i == news_id:
                        print(news['news_title'])
            print('=' * 40)

#make_all_news()
#make_km_cluster()
#content_recommend()

#make_user_news_vectors()
user_recommend()