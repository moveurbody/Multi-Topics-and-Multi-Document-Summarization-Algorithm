# -*- coding: utf-8 -*-
# @Time    : 2018/3/2 下午 03:09
# @Author  : Yuhsuan
# @File    : semantic_analysis.py
# @Software: PyCharm
import json
import re
import os
import time
import pandas as pd
from log_module import log
from doc_to_vector import*
from term_weighting import tf_pdf,cosines

# 畫圖的原件
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors

from Pajek import pajek

def main():
    # DATA = news_data_transformer()
    # relation = relatioin_analysis(DATA)

    relation={}
    with open('group_22_tf_pdf.json','r',encoding='utf8') as file:
        relation = json.load(file)

    for i in range(1,100):
        get_relation_and_draw(relation, i / 100, str(i))
        time.sleep(3)
        res = pajek(str(i)).run()
        log(i,lvl='w')
        log(res,lvl='w')

# 將原始資料做整理成方便使用的格式
def news_data_transformer():
    # 最後分群，依照原始檔案路徑的資料
    final_group_file_path = "C://Users//Yuhsuan//Desktop//MEMDS//arrange_day_0//final_group_file.json"
    # 最後分群，依照參考檔案路徑的資料
    final_group_file_reference_path = "C://Users//Yuhsuan//Desktop//MEMDS//arrange_day_0//final_group_file_reference.json"

    final_group_file = {}
    final_group_file_reference = {}

    with open(final_group_file_path,"r") as file:
        final_group_file = json.load(file)

    with open(final_group_file_reference_path,"r") as file:
        final_group_file_reference = json.load(file)

    # 計算有多少個群組
    len_group = len(final_group_file)

    res = []
    # 開始做整理資料格式
    for group_number in range(len_group):
        # 將取得的資料暫存的list
        temp_data_list = []
        for list_number in range(len(final_group_file[str(group_number)])):
            # 定義各欄位資料
            # 原始的檔案路徑
            source_file =""
            # 參考的檔案路徑
            reference_file=""
            # 計算後屬於第幾天的資料
            day_number = ""
            # 原始檔案的來源是屬於哪個新聞媒體
            news_srouce = ""
            # 原始檔案的來源是屬於哪個新聞事件
            news_event = ""
            # 發生的時間
            news_event_date=""
            # 參考檔案中的最後一個第幾天的新聞事件
            news_numer_in_day = ""

            source_file = final_group_file[str(group_number)][list_number].replace("\stemming_data","")
            reference_file = final_group_file_reference[str(group_number)][list_number]

            m1 = re.match(re.compile("(\d+) \d+.txt"),os.path.basename(source_file))
            news_event_date = m1.group(1)
            m2 = re.match(re.compile(".*day(\d+)_(.*)_(.*)_(\d+).txt"),reference_file)
            news_srouce = m2.group(2)
            news_event = m2.group(3)
            day_number = m2.group(1)
            news_numer_in_day = m2.group(4)
            temp_data_list.append([int(group_number),int(day_number),source_file,reference_file,news_srouce,news_event,news_event_date,news_numer_in_day])
        # print("group: %s\n%s" % (group_number,temp_data_list))
        # print(temp_data_list)

        res.extend(temp_data_list)
    # 儲存dataframe資料並排序
    df = pd.DataFrame(res,columns=["group","day_number","source_file","reference_file","news_srouce","news_event","news_event_date","news_numer_in_day"])
    df.sort_values(by=['group', 'day_number'], ascending=[True, True],inplace=True)
    # df.to_csv('data_group_info.csv', sep=',', encoding='utf-8')

    day_number = list(df.loc[df['group']==22]['day_number'])
    source_file = list(df.loc[df['group']==22]['source_file'])

    # 用來記錄共有多少筆資料
    file_number = len(day_number)

    # 用來記錄群組22內的資料結構-------下面
    GROUP = {}
    GROUP['group_number']=22
    GROUP['source']={}
    GROUP['steamming']={}
    GROUP['tf_pdf_group_info']=[]
    GROUP['daily_sentence_group_count']=[]
    GROUP['sentence_group'] = []

    last_sg_number=0
    worker = DocToSG('english')
    for num in range(file_number):
        lines = []
        file = open(source_file[num],'r',encoding='utf8')
        lines = file.readlines()
        file.close()

        # 計算共讀出多少行數
        line_number = len(lines)
        # sg = "d%s_sg%s" % (day_number[num], i)

        if num == 0:
            for i in range(line_number):
                sg = "d%s_sg%s" % (day_number[num], i)
                GROUP['sentence_group'].append(sg)
                GROUP['source'][sg] = lines[i]
                GROUP['steamming'][sg] = worker.ProcessText(lines[i]).split(" ")
                # 為了tf-pdf的日子加上這個屬性
                GROUP['tf_pdf_group_info'].append(day_number[num])
            last_sg_number = line_number
        if num > 0 and day_number[num]!=day_number[num-1]:
            for i in range(line_number):
                sg = "d%s_sg%s" % (day_number[num], i)
                GROUP['sentence_group'].append(sg)
                GROUP['source'][sg] = lines[i]
                GROUP['steamming'][sg] = worker.ProcessText(lines[i]).split(" ")
                # 為了tf-pdf的日子加上這個屬性
                GROUP['tf_pdf_group_info'].append(day_number[num])
            last_sg_number = line_number
        if num > 0 and day_number[num] == day_number[num - 1]:
            for i in range(line_number):
                sg = "d%s_sg%s" % (day_number[num], last_sg_number+i)
                GROUP['sentence_group'].append(sg)
                GROUP['source'][sg] = lines[i]
                GROUP['steamming'][sg] = worker.ProcessText(lines[i]).split(" ")
                # 為了tf-pdf的日子加上這個屬性
                GROUP['tf_pdf_group_info'].append(day_number[num])
            last_sg_number = line_number+last_sg_number

    items = list(set(GROUP['tf_pdf_group_info']))
    for i in items:
        count = 0
        for j in GROUP['tf_pdf_group_info']:
            if i==j:
                count = count+1
        GROUP['daily_sentence_group_count'].append(count)

    with open('group_22.json','w',encoding='utf8') as file:
        json.dump(GROUP,file)

    # 用來記錄群組22內的資料結構-------上面
    return GROUP

def relatioin_analysis(GROUP):
    #TFPDF中用來記錄屬於哪個日子用的list
    corpus_list = []

    for i in GROUP['steamming']:
        corpus_list.append(GROUP['steamming'][i])

    tf_pdf_vect = tf_pdf(corpus_list,GROUP['tf_pdf_group_info'])

    # 開始針對下一天的資料進行相似度的比較
    daily_sentence_group_count = GROUP['daily_sentence_group_count']
    # 先選取要比較的數量,reference_count是前一天的數量,compare_count是後一天的數量

    count_len = len(daily_sentence_group_count)
    last_day_count = 0
    compare_count = 0
    relation = []
    log('start cosing analysis',lvl='w')
    for i in range(count_len):
        if i == count_len - 1:
            pass
        else:
            compare_count = compare_count + daily_sentence_group_count[i]
            reference_count = compare_count + daily_sentence_group_count[i + 1]
            for j in range(1 + last_day_count, 1 + compare_count):
                for k in range(1 + compare_count, 1 + reference_count):
                    res = cosines(tf_pdf_vect[j],tf_pdf_vect[k])
                    # log("%s,%s,%s" % (GROUP['sentence_group'][j-1],GROUP['sentence_group'][k-1],res))
                    relation.append([GROUP['sentence_group'][j-1],GROUP['sentence_group'][k-1],res])
            print(1 + last_day_count, 1 + compare_count, 1 + reference_count)
            last_day_count = compare_count

    # log("\n\n\n\n", lvl="i")
    # log(relation,lvl="i")

    relation_json={}
    relation_json['relation'] = relation

    with open('group_22_tf_pdf.json','w',encoding='utf8') as file:
        json.dump(relation_json,file)

    return relation_json

def get_relation_and_draw(relation,threshold,file_name):
    edges = []
    nodes = []
    for i in relation['relation']:
        if i[2] >= threshold:
            edges.append((i[0],i[1]))
            nodes.append(i[0])
            nodes.append(i[1])

    G = nx.DiGraph()
    pos = {}

    pattern = "d(\d+)_sg(\d+)"
    pattern = re.compile(pattern)

    G.add_nodes_from(nodes)
    for node in nodes:
        m = re.match(pattern,node)
        pos[node] = [int(m.group(1)), int(m.group(2))]
    nx.draw_networkx_nodes(G,pos=pos,nodelist=nodes)

    G.add_edges_from(edges)
    nx.draw_networkx_edges(G,pos)
    nx.draw_networkx_labels(G,pos)

    nx.write_pajek(G, os.path.join(os.path.dirname(os.path.abspath(__file__)), "pajek/" + file_name + ".net"))

    fig = plt.gcf()
    fig.set_size_inches(100, 20)
    plt.axis('off')
    plt.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pajek/" + file_name + ".png"), dpi=100)
    # plt.show()
    plt.cla()

    # 主路徑分析的操作方法
    # 1. Extract the largest component from the network:
    #     a. Network > Create partition > Component > Weak
    #     b. Operations > Network + Partition > Extract subnetwork > Choose cluster 1;
    # 2. Remove strong components from the largest component:
    #     a. Network > Create partition > Component > Strong
    #     b. Operations > Network + Partition > Shrink network > [use default values]
    # 3. Remove loops:
    #     a. Network > Create new network > Transform > Remove > Loops
    #
    # 4. Create main path (or critical path):
    #     a. Network > Acyclic network > Create weighted > Traversal > SPC
    #     b. Network > Acyclic network > Create (Sub)Network > Main Paths
    # The subsequent choice among the options of Main Path for “> Global Search > Standard”,

if __name__=="__main__":
    main()