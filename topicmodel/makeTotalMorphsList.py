#-*- coding: utf-8 -*-
import pickle

with open('/home/hyeyoung/NKDB/data/result_list1.txt', 'rb') as f:
    data1 = pickle.load(f) # 단 한줄씩 읽어옴

with open('/home/hyeyoung/NKDB/data/result_list2.txt', 'rb') as f:
    data2 = pickle.load(f) # 단 한줄씩 읽어옴

with open('/home/hyeyoung/NKDB/data/result_list3.txt', 'rb') as f:
    data3 = pickle.load(f) # 단 한줄씩 읽어옴

with open('/home/hyeyoung/NKDB/data/result_list4.txt', 'rb') as f:
    data4 = pickle.load(f) # 단 한줄씩 읽어옴

with open('/home/hyeyoung/NKDB/data/result_list5.txt', 'rb') as f:
    data5 = pickle.load(f) # 단 한줄씩 읽어옴

with open('/home/hyeyoung/NKDB/data/result_list6.txt', 'rb') as f:
    data6 = pickle.load(f) # 단 한줄씩 읽어옴

with open('/home/hyeyoung/NKDB/data/result_list7.txt', 'rb') as f:
    data7 = pickle.load(f) # 단 한줄씩 읽어옴

with open('/home/hyeyoung/NKDB/data/result_list8.txt', 'rb') as f:
    data8 = pickle.load(f) # 단 한줄씩 읽어옴

with open('/home/hyeyoung/NKDB/data/result_list9.txt', 'rb') as f:
    data9 = pickle.load(f)  # 단 한줄씩 읽어옴

with open('/home/hyeyoung/NKDB/data/result_list10.txt', 'rb') as f:
    data10 = pickle.load(f)  # 단 한줄씩 읽어옴

with open('/home/hyeyoung/NKDB/data/result_list11.txt', 'rb') as f:
    data11 = pickle.load(f)  # 단 한줄씩 읽어옴

with open('/home/hyeyoung/NKDB/data/result_list12.txt', 'rb') as f:
    data12 = pickle.load(f)  # 단 한줄씩 읽어옴

with open('/home/hyeyoung/NKDB/data/result_list13.txt', 'rb') as f:
    data13 = pickle.load(f)  # 단 한줄씩 읽어옴

with open('/home/hyeyoung/NKDB/data/result_list14.txt', 'rb') as f:
    data14 = pickle.load(f)  # 단 한줄씩 읽어옴

total_morphslist = []

total_morphslist.extend(data1)
total_morphslist.extend(data2)
total_morphslist.extend(data3)
total_morphslist.extend(data4)
total_morphslist.extend(data5)
total_morphslist.extend(data6)
total_morphslist.extend(data7)
total_morphslist.extend(data8)
total_morphslist.extend(data9)
total_morphslist.extend(data10)
total_morphslist.extend(data11)
total_morphslist.extend(data12)
total_morphslist.extend(data13)
total_morphslist.extend(data14)

print(len(total_morphslist))

with open('/home/hyeyoung/NKDB/data/total_morphs_list.txt', 'wb') as f:
    pickle.dump(total_morphslist, f)

