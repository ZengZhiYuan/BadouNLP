# -*- coding: utf-8 -*-

import json
import re
import os
import torch
import numpy as np
import csv
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer
"""
数据加载
"""


class DataGenerator:
    def __init__(self, data_path, config):
        self.config = config
        self.path = data_path
        self.index_to_label = {0: '家居', 1: '房产', 2: '股票', 3: '社会', 4: '文化',
                               5: '国际', 6: '教育', 7: '军事', 8: '彩票', 9: '旅游',
                               10: '体育', 11: '科技', 12: '汽车', 13: '健康',
                               14: '娱乐', 15: '财经', 16: '时尚', 17: '游戏'}
        self.label_to_index = dict((y, x) for x, y in self.index_to_label.items())
        self.config["class_num"] = len(self.index_to_label)
        if self.config["model_type"] == "bert":
            self.tokenizer = BertTokenizer.from_pretrained(config["bert_model_path"])
        self.vocab = load_vocab(config["bert_vocab_path"])
        self.config["vocab_size"] = len(self.vocab)
        self.load()


    def load(self):
        self.data = []
        with open(self.path, "r", encoding="utf8") as f:
            for line in f:
                lable = json.loads(line)
                tag = line["tag"]
                label = self.label_to_index[tag]
                title = line["title"]
                if self.config["model_type"] == "bert":
                    input_id = self.tokenizer.encode(title, max_length=self.config["max_length"], pad_to_max_length=True)
                else:
                    input_id = self.encode_sentence(title)
                input_id = torch.LongTensor(input_id)
                label_index = torch.LongTensor([label])
                self.data.append([input_id, label_index])
        return

    def encode_sentence(self, text):
        input_id = []
        for char in text:
            input_id.append(self.vocab.get(char, self.vocab["[UNK]"]))
        input_id = self.padding(input_id)
        return input_id

    #补齐或截断输入的序列，使其可以在一个batch内运算
    def padding(self, input_id):
        input_id = input_id[:self.config["max_length"]]
        input_id += [0] * (self.config["max_length"] - len(input_id))
        return input_id

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        return self.data[index]



def load_vocab(vocab_path):
    token_dict = {}
    with open(vocab_path, encoding="utf8") as f:
        for index, line in enumerate(f):
            token = line.strip()
            token_dict[token] = index + 1  #0留给padding位置，所以从1开始
    return token_dict


class BertDataSet(Dataset):
    def __init__(self,config,file_path):
        self.tokenizer = BertTokenizer.from_pretrained(config["bert_model_path"])
        self.data = []
        self.load_data(config,file_path)
    def __getitem__(self, index):
        data = self.data[index]
        # print(index)
        return data

    def __len__(self):
        return len(self.data)

    def load_data(self,config,file_path):
       with open(file_path, encoding="utf8") as f:
           reader = csv.DictReader(f)
           for row in reader:
               label = row['label']
               review = row['review']
               review_id = self.tokenizer.encode(review, max_length=config["max_length"], padding='max_length')
               review_id = torch.LongTensor(review_id)
               labelType = torch.LongTensor([int(label)])
               self.data.append([review_id, labelType])
       return

# 会被多个方法调用，文件路径由方法提供
def bert_load_data(config,file_path,shuffle):
    # 创建BertDataSet对象，用于加载数据
    dataset = BertDataSet(config,file_path)
    # 创建DataLoader对象，用于将数据集分成批次，并打乱顺序
    dataloader = DataLoader(dataset, batch_size=config["batch_size"], shuffle=shuffle)
    # 返回DataLoader对象
    return dataloader

def bert_load_vocab():
    token_dict = {}
    with open(Config["bert_vocab_path"], encoding="utf8") as f:
        for index, line in enumerate(f):
            token = line.strip()
            token_dict[token] = index + 1  #0留给padding位置，所以从1开始
    return token_dict

def jieba_load_vocab():
    token_dict = {}
    with open(Config["jieba_vocab_path"], encoding="utf8") as f:
        for index, line in enumerate(f):
            token = line.strip().split()[0]
            token_dict[token] = index + 1  #0留给padding位置，所以从1开始
    return token_dict

#用torch自带的DataLoader类封装数据
def load_data(data_path, config, shuffle=True):
    dg = DataGenerator(data_path, config)
    dl = DataLoader(dg, batch_size=config["batch_size"], shuffle=shuffle)
    return dl

if __name__ == "__main__":
    from config import Config
    dg = DataGenerator("valid_tag_news.json", Config)
    print(dg[1])
