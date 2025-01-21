from collections import namedtuple
import numpy as np
import torch as th
import json
import torch
import datetime
import copy
import random


class MinMaxNormalization(object):
    """
        MinMax Normalization --> [-1, 1]
        x = (x - min) / (max - min).
        x = x * 2 - 1
    """

    def __init__(self):
        pass

    def fit(self, X):
        self._min = X.min()
        self._max = X.max()
        print("min:", self._min, "max:", self._max)

    def transform(self, X):
        X = 1. * (X - self._min) / (self._max - self._min)
        X = X * 2. - 1.
        return X

    def fit_transform(self, X):
        self.fit(X)
        return self.transform(X)

    def inverse_transform(self, X):
        X = (X + 1.) / 2.
        X = 1. * X * (self._max - self._min) + self._min
        return X



def data_load_single(args, dataset): 

    folder_path = '{}'.format(dataset)
    f = open(folder_path,'r')
    data_all = json.load(f)

    X_train = torch.tensor(data_all['X_train'][0]).unsqueeze(1)
    X_test = torch.tensor(data_all['X_test'][0]).unsqueeze(1)
    X_val = torch.tensor(data_all['X_val'][0]).unsqueeze(1)

    X_train_period = torch.tensor(data_all['X_train'][1]).permute(0,2,1,3,4)
    X_test_period = torch.tensor(data_all['X_test'][1]).permute(0,2,1,3,4)
    X_val_period = torch.tensor(data_all['X_val'][1]).permute(0,2,1,3,4)

    args = args._replace(seq_len = X_train.shape[2])
    H, W = X_train.shape[3], X_train.shape[4]  

    X_train_ts = data_all['timestamps']['train']
    X_test_ts = data_all['timestamps']['test']
    X_val_ts = data_all['timestamps']['val']

    X_train_ts = torch.tensor([[((i%(24*2*7)//(24*2)+2)%7,i%(24*2)) for i in t] for t in X_train_ts])
    X_test_ts = torch.tensor([[((i%(24*2*7)//(24*2)+2)%7, i%(24*2)) for i in t] for t in X_test_ts])
    X_val_ts = torch.tensor([[((i%(24*2*7)//(24*2)+2)%7, i%(24*2)) for i in t] for t in X_val_ts])

    reconstruct = [X_train[[0], :, :, :, :]]
    for i in range(1, X_train.shape[0]):
        reconstruct.append(X_train[[i], :, [11], :, :].unsqueeze(2))
    reconstruct_train = torch.cat(reconstruct, dim=2)
    np.savez("/home/seyed/PycharmProjects/step/FlashST/data/crowd/crowd_train.npz", data=reconstruct_train.squeeze(0).squeeze(0).reshape(-1, 320))
    reconstruct = [X_val[[0], :, :, :, :]]
    for i in range(1, X_val.shape[0]):
        reconstruct.append(X_val[[i], :, [11], :, :].unsqueeze(2))
    reconstruct_valid = torch.cat(reconstruct, dim=2)
    np.savez("/home/seyed/PycharmProjects/step/FlashST/data/crowd/crowd_valid.npz", data=reconstruct_valid.squeeze(0).squeeze(0).reshape(-1, 320))
    reconstruct = [X_test[[0], :, :, :, :]]
    for i in range(1, X_test.shape[0]):
        reconstruct.append(X_test[[i], :, [11], :, :].unsqueeze(2))
    reconstruct_test = torch.cat(reconstruct, dim=2)
    np.savez("/home/seyed/PycharmProjects/step/FlashST/data/crowd/crowd_test.npz", data=reconstruct_test.squeeze(0).squeeze(0).reshape(-1, 320))
    my_scaler = MinMaxNormalization()
    MAX = max(torch.max(X_train).item(), torch.max(X_test).item(), torch.max(X_val).item())
    MIN = min(torch.min(X_train).item(), torch.min(X_test).item(), torch.min(X_val).item())
    my_scaler.fit(np.array([MIN, MAX]))

    X_train = my_scaler.transform(X_train.reshape(-1,1)).reshape(X_train.shape)
    X_test = my_scaler.transform(X_test.reshape(-1,1)).reshape(X_test.shape)
    X_val = my_scaler.transform(X_val.reshape(-1,1)).reshape(X_val.shape)
    X_train_period = my_scaler.transform(X_train_period.reshape(-1,1)).reshape(X_train_period.shape)
    X_test_period = my_scaler.transform(X_test_period.reshape(-1,1)).reshape(X_test_period.shape)
    X_val_period = my_scaler.transform(X_val_period.reshape(-1,1)).reshape(X_val_period.shape)

    data = [[X_train[i], X_train_ts[i], X_train_period[i]] for i in range(X_train.shape[0])]
    test_data = [[X_test[i], X_test_ts[i], X_test_period[i]] for i in range(X_test.shape[0])]
    val_data = [[X_val[i], X_val_ts[i], X_val_period[i]] for i in range(X_val.shape[0])]

    if args.mode == 'few-shot':
        data = data[:int(len(data)*args.few_ratio)]
    batch_size = args.batch_size
    if H + W < 32:
        batch_size = args.batch_size_1
    elif H + W < 48:
        batch_size = args.batch_size_2
    elif H + W < 64:
        batch_size = args.batch_size_3

    data = th.utils.data.DataLoader(data, num_workers=4, batch_size=batch_size, shuffle=True) 
    test_data = th.utils.data.DataLoader(test_data, num_workers=4, batch_size = 4 * batch_size, shuffle=False)
    val_data = th.utils.data.DataLoader(val_data, num_workers=4, batch_size = 4 * batch_size, shuffle=False)

    return  data, test_data, val_data, my_scaler


Args = namedtuple('Args', ['task', "seq_len"])
args = Args('short', None)


data_load_single(args, "/home/seyed/forked/UniST/dataset/Crowd_short.json")