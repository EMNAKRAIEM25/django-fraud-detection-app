#!/usr/bin/env python
# coding: utf-8

# In[83]:


import pandas as pd


# In[84]:


df=pd.read_csv("Udacity.csv")


# In[85]:


df.info()


# In[86]:


df.head()


# In[87]:


df_rating = df.sort_values(by='Rating', ascending=False) 


# In[88]:


df_rating.head()


# In[89]:


df_rating[df_rating['Rating'] != 'None'].head(10)


# In[90]:


df_rating1 = df_rating.drop(['Link', 'School'], axis=1)
df_rating1.head(10)


# In[91]:


from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from IPython.display import display

# In[92]:


df_rating1.shape


# In[93]:


df_rating1 = df_rating1.dropna()

df_rating1.head(10)


# In[94]:


df_rating1.shape


# In[95]:


df_rating2 = df_rating1.head(100)


# In[96]:


df_rating2["About"].head(10)


# In[97]:


import pandas as pd
import numpy as np

import spacy
import en_core_web_sm
nlp = en_core_web_sm.load()

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sklearn.decomposition import TruncatedSVD

import matplotlib.pyplot as plt
import wordcloud


# In[98]:


print('Description of the first about : ',df_rating1.loc[0,'About'])


# In[99]:


# Remove HTML elements
df_rating1['clean_description'] = df_rating1['About'].str.replace(r"<[a-z/]+>", " ") 
# Remove special characters and numbers
df_rating1['clean_description'] = df_rating1['clean_description'].str.replace(r"[^A-Za-z]+", " ") 
print('Description cleaned of the first about : ',df_rating1.loc[0,'clean_description'])


# In[100]:


df_rating1['clean_description'] = df_rating1['clean_description'].str.lower()
print('Description in lower case of the first about : ',df_rating1.loc[0,'clean_description'])


# In[101]:


## Tokenize the cleaned description
df_rating1['clean_tokens'] = df_rating1['clean_description'].apply(lambda x: nlp(x))
df_rating1.head()


# In[102]:


# Remove stop words
from spacy.lang.en.stop_words import STOP_WORDS

df_rating1['clean_tokens'] = df_rating1['clean_tokens'].apply(lambda x: [token.lemma_ for token in x if token.text not in STOP_WORDS])
df_rating1.head()


# In[103]:


# Put back tokens into one single string
df_rating1["clean_document"] = [" ".join(x) for x in df_rating1['clean_tokens']]
df_rating1.head()


# In[104]:


# TF-IDF vector
vectorizer = TfidfVectorizer(stop_words='english')
X = vectorizer.fit_transform(df_rating1["clean_document"])

# X is a generator. We can transform that as an array
X = X.toarray()
print(X.shape)


# In[105]:


# Print the 50 first words into our vocabulary
print(sorted(vectorizer.vocabulary_.items())[:50])


# In[106]:


# Create a dataframe with tf-idf
X_df = pd.DataFrame(X, 
             columns=vectorizer.get_feature_names_out(), 
             index=["item_{}".format(x) for x in range(df_rating1.shape[0])] )

X_df.head()


# In[107]:


# Clustering on documents with DBSCAN
clustering = DBSCAN(eps=0.7, min_samples=3, metric="cosine", algorithm="brute")

# Fit on data 
#No need to normalize data, it already is due to TF-IDF
clustering.fit(X)

# Write cluster ids into df_rating1 and X_df
df_rating1['cluster_id'] = clustering.labels_
display(df_rating1.head())
X_df['cluster_id'] = clustering.labels_
display(X_df.head())


# In[108]:


# Number of documents in each cluster
df_rating1['cluster_id'].value_counts()


# In[109]:


# Print sample of 3 documents for the 5 first cluster
for c in df_rating1['cluster_id'].value_counts().index[:5] :
    print("CLUSTER ", c , ' :')
    print('----')
    for d in df_rating1.loc[df_rating1['cluster_id']==c,:].sample(3)['clean_description']:
        print(d)
        print()
    print('-----------')


# In[110]:


# 5 Most frequent words in each cluster
cols = [c for c in X_df.columns if c!='cluster_id']

for c in df_rating1['cluster_id'].value_counts().index[:5] :
    print("CLUSTER ", c)
    print(X_df.loc[X_df['cluster_id']==c,cols].mean(axis=0).sort_values(ascending=False)[0:5])
    print('-----------')

# In[114]:


# Create a new column with index values
df_rating1['id'] = df_rating1.index
print(df_rating1)
from typing import List

def find_similar_items(item_id):
    cluster_id = df_rating1.loc[df_rating1['id'] == item_id, 'cluster_id'].values[0]
    cluster_items = df_rating1.loc[df_rating1['cluster_id'] == cluster_id, :]
    cluster_size = len(cluster_items)
    sample_size = min(5, cluster_size)
    similar_items = cluster_items.sample(sample_size)
    similar_item_ids = similar_items['id'].unique() if sample_size > 0 else []
    return similar_item_ids
# For printing in colors
class bcolors:
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
def print_similar_items(item_id) :
    try:
        item = df_rating1.loc[df_rating1['id'] == item_id]
        if item.empty:
            raise Exception("Formation not found in the database. Please enter a valid formation_id")

        item_desc = item['clean_description'].values[0]
        item_rating = item['Rating'].values[0]
        similar_item_ids = find_similar_items(item_id)

        print(f"{bcolors.OKBLUE}Formation found in the database, description below:")
        print(item_desc)
        print(f"Rating: {item_rating}")
        print()

        print("Based on the analysis of the descriptions, you might also be interested in the following descriptions:")
        print()

        for i in similar_item_ids:
            similar_item_desc = df_rating1.loc[df_rating1['id'] == i, 'clean_description'].values[0]
            similar_item_rating = df_rating1.loc[df_rating1['id'] == i, 'Rating'].values[0]
            print(f"{bcolors.OKGREEN}Item #{i}")
            print(similar_item_desc)
            print(f"Rating: {similar_item_rating}")
            print('--------------------')

        return item_desc
    except Exception as e:
        print(str(e))
        return None

# Example usage
#item_id = int(input("What formation would you like to choose? "))
#print_similar_items(item_id)




