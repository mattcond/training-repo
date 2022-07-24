# %% import pkg

from peewee import MySQLDatabase
import pandas as pd
import seaborn as sns
sns.set(rc={'figure.figsize':(20,20)})

import matplotlib.pyplot as plt



# %% MYSQL CONNECTION

config = {
  'user': 'scraper',
  'password': 's:a6:sFcNP^:A',
  'host': '212.237.39.83',
  'database': 'immo_data'
}

cnx = MySQLDatabase('immo_data', 
                   user='scraper', 
                   password='s:a6:sFcNP^:A',
                   host='212.237.39.83', 
                   port=3306)
   
annuncio = pd.read_sql('select * from annuncio', cnx)
dettaglio = pd.read_sql('select * from dettaglio', cnx)
reversegeo = pd.read_sql('select * from reversegecodingad', cnx)

annuncio.to_parquet('data/input/annuncio.parquet')
dettaglio.to_parquet('data/input/dettaglio.parquet')
reversegeo.to_parquet('data/input/reversegeo.parquet')

merge_dataset = pd.merge(annuncio, dettaglio, on='url_id', suffixes=('_ann', '_dett'))
merge_dataset = pd.merge(merge_dataset, reversegeo, on='url_id', suffixes=('', '_rga'))

merge_dataset.to_parquet('data/input/merge_dataset.parquet')

cnx.close()

# %% Read data

annuncio = pd.read_parquet('data/input/annuncio.parquet')
dettaglio = pd.read_parquet('data/input/dettaglio.parquet')
merge_dataset = pd.read.read_parquet('data/input/merge_dataset.parquet')


# %% EDA

merge_dataset.head(1).T
merge_dataset.dtypes

sns.catplot('affitto', kind = 'count', data=merge_dataset)
sns.catplot('affitto', kind = 'count', data=merge_dataset.loc[merge_dataset.sigla =='BO'])
sns.catplot('affitto', kind = 'count', data=merge_dataset.loc[merge_dataset.comune_rga =='Bologna'])

sns.catplot(x='sigla',  kind = 'count', data = merge_dataset)

sns.catplot(x='tipo_immobile',  
            kind = 'count', 
            data = merge_dataset, 
            order=merge_dataset['tipo_immobile'].value_counts().index)

sns.catplot(x='tipo_proprietà',  
            kind = 'count', 
            data = merge_dataset, 
            order=merge_dataset['tipo_proprietà'].value_counts().index)

sns.catplot(x='piano',  
            kind = 'count', 
            data = merge_dataset, 
            order=merge_dataset['piano'].value_counts().index)

