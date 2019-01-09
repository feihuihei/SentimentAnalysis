#! /bin/env python
# -*- coding: utf-8 -*-
"""
ѵ�����磬������ģ�ͣ�����LSTM��ʵ�ֲ���Python�е�keras��
"""
import pandas as pd 
import numpy as np 
import jieba
import multiprocessing

from gensim.models.word2vec import Word2Vec
from gensim.corpora.dictionary import Dictionary
from keras.preprocessing import sequence

from sklearn.cross_validation import train_test_split
from keras.models import Sequential
from keras.layers.embeddings import Embedding
from keras.layers.recurrent import LSTM
from keras.layers.core import Dense, Dropout,Activation
from keras.models import model_from_yaml
np.random.seed(1337)  # For Reproducibility
import sys
sys.setrecursionlimit(1000000)
import yaml

# set parameters:
cpu_count = multiprocessing.cpu_count() # 4
vocab_dim = 100
n_iterations = 1  # ideally more..
n_exposures = 10 # ����Ƶ������10�Ĵ���
window_size = 7
n_epoch = 4
input_length = 100
maxlen = 100

batch_size = 32


def loadfile():
    neg=pd.read_csv('../data/neg.csv',header=None,index_col=None)
    pos=pd.read_csv('../data/pos.csv',header=None,index_col=None,error_bad_lines=False)
    neu=pd.read_csv('../data/neutral.csv', header=None, index_col=None)

    combined = np.concatenate((pos[0], neu[0], neg[0]))
    y = np.concatenate((np.ones(len(pos), dtype=int), np.zeros(len(neu), dtype=int), 
                        -1*np.ones(len(neg),dtype=int)))

    return combined,y


#�Ծ��Ӿ��зִʣ���ȥ�����з�
def tokenizer(text):
    ''' Simple Parser converting each document to lower-case, then
        removing the breaks for new lines and finally splitting on the
        whitespace
    '''
    text = [jieba.lcut(document.replace('\n', '')) for document in text]
    return text


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
        print ('No data provided...')


#���������ֵ䣬������ÿ����������������������Լ�ÿ����������Ӧ�Ĵ�������
def word2vec_train(combined):

    model = Word2Vec(size=vocab_dim,
                     min_count=n_exposures,
                     window=window_size,
                     workers=cpu_count,
                     iter=n_iterations)
    model.build_vocab(combined) # input: list
    model.train(combined)
    model.save('../lstm_data_test/Word2vec_model.pkl')
    index_dict, word_vectors,combined = create_dictionaries(model=model,combined=combined)
    return   index_dict, word_vectors,combined


def get_data(index_dict,word_vectors,combined,y):

    n_symbols = len(index_dict) + 1  # ���е��ʵ���������Ƶ��С��10�Ĵ�������Ϊ0�����Լ�1
    embedding_weights = np.zeros((n_symbols, vocab_dim)) # ��ʼ�� ����Ϊ0�Ĵ��������ȫΪ0
    for word, index in index_dict.items(): # ������Ϊ1�Ĵ��￪ʼ����ÿ�������Ӧ�������
        embedding_weights[index, :] = word_vectors[word]
    x_train, x_test, y_train, y_test = train_test_split(combined, y, test_size=0.2)
    y_train = keras.utils.to_categorical(y_train,num_classes=3) 
    y_test = keras.utils.to_categorical(y_test,num_classes=3)
    # print x_train.shape,y_train.shape
    return n_symbols,embedding_weights,x_train,y_train,x_test,y_test


##��������ṹ
def train_lstm(n_symbols,embedding_weights,x_train,y_train,x_test,y_test):
    print ('Defining a Simple Keras Model...')
    model = Sequential()  # or Graph or whatever
    model.add(Embedding(output_dim=vocab_dim,
                        input_dim=n_symbols,
                        mask_zero=True,
                        weights=[embedding_weights],
                        input_length=input_length))  # Adding Input Length
    model.add(LSTM(output_dim=50, activation='tanh'))
    model.add(Dropout(0.5))
    model.add(Dense(3, activation='softmax')) # Dense=>ȫ���Ӳ�,���ά��=3
    model.add(Activation('softmax'))

    print ('Compiling the Model...')
    model.compile(loss='categorical_crossentropy',
                  optimizer='adam',metrics=['accuracy'])

    print ("Train..." )# batch_size=32
    model.fit(x_train, y_train, batch_size=batch_size, epochs=n_epoch,verbose=1)

    print ("Evaluate...")
    score = model.evaluate(x_test, y_test,
                                batch_size=batch_size)

    yaml_string = model.to_yaml()
    with open('../model/lstm.yml', 'w') as outfile:
        outfile.write( yaml.dump(yaml_string, default_flow_style=True) )
    model.save_weights('../model/lstm.h5')
    print ('Test score:', score)


#ѵ��ģ�ͣ�������
print ('Loading Data...')
combined,y=loadfile()
print (len(combined),len(y))
print ('Tokenising...')
combined = tokenizer(combined)
print ('Training a Word2vec model...')
index_dict, word_vectors,combined=word2vec_train(combined)

print ('Setting up Arrays for Keras Embedding Layer...')
n_symbols,embedding_weights,x_train,y_train,x_test,y_test=get_data(index_dict, word_vectors,combined,y)
print ("x_train.shape and y_train.shape:")
print (x_train.shape,y_train.shape)
train_lstm(n_symbols,embedding_weights,x_train,y_train,x_test,y_test)