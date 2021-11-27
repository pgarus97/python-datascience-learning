import os
import sys

import pandas as pd
from keybert import KeyBERT
from pandas import json_normalize
import json


def count_keys(selected_key, val, obj):
    count = 0

    # iterate arrays
    if isinstance(obj, list):
        for item in obj:
            count += count_keys(selected_key, val, item)
    # iterate objects
    elif isinstance(obj, dict):
        for key in obj:

            if key == selected_key:
                value = val


                if value in str(obj[key]):
                    count += 1

            count += count_keys(selected_key, val, obj[key])

    return count

def getDataFrame(path):
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)

    with open(path,
              "r") as read_file:
        jsondata = json.loads(read_file.read())

        # gets datagram
        dataframe = json_normalize(jsondata['messages'])
        #glomdata = glom(jsondata, ('messages', [('blocks',[('elements', [('elements', ['type'])])])]))
        return dataframe

def print_dataframe_csv(dataframe, save_path, filename):
    dataframe = dataframe.replace(r'\n', ' ', regex=True)
    dataframe.to_csv(save_path + filename + '.csv')

def messages_to_txt(dataframe, save_path, filename):
    text_subtype = dataframe[["text", "subtype"]]
    messageframe = text_subtype[pd.isna(text_subtype['subtype'])]
    messageframe.to_csv(save_path + filename + '.txt', sep='\t', index=False, header=False)

def extract_information(dataframe, save_path, filename):
    dictframe = dataframe.to_dict(orient='records')

    count_channeljoin = len(dataframe.loc[dataframe['subtype'] == 'channel_join'])
    count_channelpurpose = len(dataframe.loc[dataframe['subtype'] == 'channel_purpose'])
    count_messages = len(dataframe[pd.isna(dataframe['subtype'])])
    count_active_user = len(dataframe['user'].unique())
    count_team = len(dataframe['team'].dropna().unique())
    most_active_user = dataframe['user'].value_counts().idxmax()
    count_reactions = len(dataframe['reactions'].dropna())
    count_emoji = count_keys('type','emoji',dictframe)
    count_link = count_keys('type','link',dictframe)
    count_mentions = count_keys('type','user', dictframe)

    with open("datasets/messagetext_dataset/"+filename+".txt",
              "r") as txt_file:
        messagetxt = txt_file.read()

    kw_model = KeyBERT()
    print("Processing keywords of: " + filename)
    keywords = kw_model.extract_keywords(messagetxt, keyphrase_ngram_range=(1, 1), stop_words=None)
    print("Processing keypairs of: " + filename)
    keypairs = kw_model.extract_keywords(messagetxt, keyphrase_ngram_range=(1, 2), stop_words=None)


    #dict with all needed information
    info = {
        "count_channeljoin" : count_channeljoin,
        "count_channelpurpose" : count_channelpurpose,
        "count_messages" : count_messages,
        "count_active_user" : count_active_user,
        "count_team" : count_team,
        "most_active_user" : most_active_user,
        "count_reactions" : count_reactions,
        "count_emoji" : count_emoji,
        "count_link" : count_link,
        "count_mentions" :count_mentions,
        "keywords" : keywords,
        "keypairs" : keypairs
    }

    with open(save_path+filename+".json", "w") as out:
        json.dump(info, out, indent=2)

if __name__ == '__main__':

    dataset_path = sys.argv[1]
    #create directory for txt files
    if not os.path.exists('datasets/mainframe_dataset'):
        os.mkdir('datasets/mainframe_dataset')

    if not os.path.exists('datasets/messagetext_dataset'):
        os.mkdir('datasets/messagetext_dataset')

    if not os.path.exists('datasets/information_dataset'):
        os.mkdir('datasets/information_dataset')

    #iterate through all json files in dataset
    for filename in os.listdir(dataset_path):
        if filename.endswith(".json"):
            dataframe = getDataFrame(dataset_path+filename)
            print("Processing main dataframe of: " + filename)
            print_dataframe_csv(dataframe, "datasets/mainframe_dataset/", filename.replace('.json', ''))
            print("Processing text messages of: " + filename)
            messages_to_txt(dataframe, "datasets/messagetext_dataset/", filename.replace('.json', ''))
            print("Processing meta information of: " + filename)
            extract_information(dataframe, "datasets/information_dataset/", filename.replace('.json', ''))


