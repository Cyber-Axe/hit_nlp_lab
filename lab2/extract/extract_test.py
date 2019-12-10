from extract.extract_train import create_model, Label_Lst, Test_Reviews, Answer_File, Max_Len
from keras.preprocessing.sequence import pad_sequences
import pandas as pd
import jieba
import csv


def run_model():
    model, vocab = create_model(train=False)
    model.load_weights('../model/extract/extract.h5')  # 加载模型
    test_csv_txt = pd.read_csv(Test_Reviews)  # 读取测试文本
    review_lst = [jieba.lcut(review) for review in test_csv_txt['Review']]
    idx_lst = [idx for idx in test_csv_txt['id']]
    word2idx = dict((word, idx) for idx, word in enumerate(vocab))  # 获得字到序号的索引
    data = [[word2idx.get(word.lower(), 0) for word in review] for review in review_lst]
    data = pad_sequences(data, Max_Len)  # n行，Max_Len列
    result = model.predict_classes(data)  # 得到标注列表，行如[[0,0],[1,2],[0,3]]
    tag_lst = []  # 标注结果，n行，len列
    for review, line in zip(review_lst, result):
        tag_lst.append(Label_Lst[idx] for idx in list(line[-len(review):]))
    return review_lst, tag_lst, idx_lst  # 返回值形如['还不错','快递真快，物流真不错'][['B-ASP',O],['B-ASP','I-ASP']]


def get_match():  # 得到关键词对应的匹配关系
    review_lst, tag_lst, idx_lst = run_model()
    idx2match = {idx + 1: [] for idx in range(len(review_lst))}  # 初始化结果词典
    for i, words, tags in zip(idx_lst, review_lst, tag_lst):
        asp, opi, tags = '', '', list(tags)
        for j, (word, tag) in enumerate(zip(words, tags)):
            if (tag == 'I-ASP' and asp == '') or (tag == 'I-OPI' and opi == ''):
                if tag == 'I-ASP' and 'OPI' not in tags[j - 1] and words[j - 1] not in (' ', '，'):
                    asp += words[j - 1]
                if tag == 'I-OPI' and 'ASP' not in tags[j - 1] and words[j - 1] not in (' ', '，'):
                    opi += words[j - 1]
            if tag in ('B-ASP', 'I-ASP') or tag in ('B-OPI', 'I-OPI'):
                asp += word if tag in ('B-ASP', 'I-ASP') else ''
                opi += word if tag in ('B-OPI', 'I-OPI') else ''
            else:
                if opi:
                    asp = '_' if not asp else asp
                    idx2match[i].append((asp, opi))  # 加入结果列表中
                    asp, opi = '', ''
        if asp or opi:
            match = (asp, '_') if not opi else ('_', opi)
            match = (asp, opi) if asp and opi else match  # 如果两者均非空
            idx2match[i].append(match)
    return idx2match, idx_lst  # 返回值形如{1:[('快递'，'很快'),('包装','不错)],2:[('_','还不错')]}


def write2file():
    idx2match, idx_lst = get_match()
    result_lst = []
    with open(Answer_File, 'w', encoding='utf-8', newline='') as f:
        for idx in idx_lst:
            for match in idx2match[idx]:
                result_lst.append([idx, match[0], match[1]])
        writer = csv.writer(f)
        writer.writerows(result_lst)


if __name__ == '__main__':
    write2file()  # 写入文件
