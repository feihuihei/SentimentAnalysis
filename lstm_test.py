#! /bin/env python
# -*- coding: utf-8 -*-
"""
Ԥ��
"""
import jieba
import numpy as np
from gensim.models.word2vec import Word2Vec
from gensim.corpora.dictionary import Dictionary
from keras.preprocessing import sequence

import yaml
from keras.models import model_from_yaml
np.random.seed(1337)  # For Reproducibility
import sys
sys.setrecursionlimit(1000000)

# define parameters
maxlen = 100

def create_dictionaries(model=None,
                        combined=None):
    ''' Function does are number of Jobs:
        1- Creates a word to index mapping
        2- Creates a word to vector mapping
        3- Transforms the Training and Testing Dictionaries

    '''
    if (combined is not None) and (model is not None):
        gensim_dict = Dictionary()
        gensim_dict.doc2bow(model.vocab.keys(),
                            allow_update=True)
        #  freqxiao10->0 ����k+1
        w2indx = {v: k+1 for k, v in gensim_dict.items()}#����Ƶ������10�Ĵ��������,(k->v)=>(v->k)
        w2vec = {word: model[word] for word in w2indx.keys()}#����Ƶ������10�Ĵ���Ĵ�����, (word->model(word))

        def parse_dataset(combined): # �հ�-->��ʱʹ��
            ''' Words become integers
            '''
            data=[]
            for sentence in combined:
                new_txt = []
                for word in sentence:
                    try:
                        new_txt.append(w2indx[word])
                    except:
                        new_txt.append(0) # freqxiao10->0
                data.append(new_txt)
            return data # word=>index
        combined=parse_dataset(combined)
        combined= sequence.pad_sequences(combined, maxlen=maxlen)#ÿ���������������Ӧ�����������Ծ����к���Ƶ��С��10�Ĵ������Ϊ0
        return w2indx, w2vec,combined
    else:
        print 'No data provided...'


def input_transform(string):
    words=jieba.lcut(string)
    words=np.array(words).reshape(1,-1)
    model=Word2Vec.load('../model/Word2vec_model.pkl')
    _,_,combined=create_dictionaries(model,words)
    return combined


def lstm_predict(string):
    print 'loading model......'
    with open('../model/lstm.yml', 'r') as f:
        yaml_string = yaml.load(f)
    model = model_from_yaml(yaml_string)

    print 'loading weights......'
    model.load_weights('../model/lstm.h5')
    model.compile(loss='categorical_crossentropy',
                  optimizer='adam',metrics=['accuracy'])
    data=input_transform(string)
    data.reshape(1,-1)
    #print data
    result=model.predict_classes(data)
    # print result # [[1]]
    if result[0]==1:
        print string,' positive'
    elif result[0]==0:
        print string,' neural'
    else:
        print string,' negative'


if __name__=='__main__':
    # string='�Ƶ�Ļ����ǳ��ã��۸�Ҳ���ˣ�ֵ���Ƽ�'
    # string='�ֻ�����̫���ˣ�ɵ�Ƶ�ң�׬����Ǯ���Ժ���Ҳ��������'
    # string = "�����ҿ�������д�ú������飬��Ϊ���ˣ������������ӿ����ˣ�����������˵���ã����֡����ݡ��ṹ������"
    # string = "��˵��ְ��ָ���飬����д���е��ɬ���Ҷ�һ��Ϳ�����ȥ�ˣ�"
    # string = "����������ã���������ʵ��û��˼������Ϊ�����������ķ�������ʵ�����ǻ��������ݡ�"
    # string = "����̫��"
    # string = "������"
    string = "���һ�㣬ûʲô����ѧϰ��"
    
    lstm_predict(string)