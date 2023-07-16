# %% import pkg

from peewee import MySQLDatabase
import pandas as pd

import geopandas as gpd
from shapely.geometry import Point

import seaborn as sns
import re

import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# %%  PAR

days_window = 1000

date_par = datetime.today() - timedelta(days=days_window)
date_par = date_par.strftime('%Y-%m-%d')
print(date_par)

bologna_shp = gpd.read_file('./shapefile/aree-statistiche.geojson')

# %% FUNCTION

def normalize_riscaldamento(s):

    alim_re = re.compile('aliment')
    centr_aut_re = re.compile('autonomo|centralizzato', re.RegexFlag.IGNORECASE)

    autonomo_re = re.compile('autonomo', re.RegexFlag.IGNORECASE)

    _ret_dict = {'riscaldamento_centralizzato_cat':'', 'riscaldamento_tipo_cat':'', 'riscaldamento_alimentazione_cat':''}
    _split_val = [i.strip() for i in s.split(',')]
    #print(_split_val)

    _alim_value = list(filter(alim_re.search, _split_val))
    _centr_aut = list(filter(centr_aut_re.search, _split_val))

    if _alim_value != []:

        _alim_value = _alim_value[0]

        _split_val.remove(_alim_value)

        _alim_value = re.sub(string = _alim_value, repl='', pattern='aliment.*( a)? ', flags=re.RegexFlag.IGNORECASE)

        _ret_dict['riscaldamento_alimentazione_cat'] =  _alim_value

    if _centr_aut != []:

        _centr_aut_value = _centr_aut[0]
        _split_val.remove(_centr_aut_value)

        if autonomo_re.findall(_centr_aut_value):

            _ret_dict['riscaldamento_centralizzato_cat'] =  'NO'

        else:

            _ret_dict['riscaldamento_centralizzato_cat'] =  'SI'
    
    if _split_val != []:

        _ret_dict['riscaldamento_tipo_cat'] = _split_val[0]

    return(_ret_dict)

def normalize_year(y):

    if str(y) == '1900' or str(y) == 'None' or str(y).strip() == '':

        return '0_NO_ANNO'
    
    if str(y) <= '1950':

        return '1_ANTE_1950'
    
    if str(y) == '1950':

        return '2_1950'
    
    if str(y) <= '1960':

        return '3_1950_1960'
    
    if str(y) < '1970':

        return '4_1960_1970'

    if str(y) == '1970':

        return '5_1970'
    
    if str(y) < '1990':

        return '6_1970_1990'

    if str(y) < '2010':

        return '7_1990_2010'

    return '8_POST_2010'

def get_esposizione(s=''):

    _l = ['ovest', 'nord', 'sud', 'est']
    _o = {i:0 for i in _l}

    for c in _l:

        if c in s:

            _o[c] = 1
            s = s.replace(c, '')

    return _o 

def get_geo_info(p, shp):

    _ = shp.loc[shp.geometry.apply(lambda x: x.contains(p)), ['codice_area_statistica', 'area_statistica', 'cod_quar', 'quartiere', 'cod_zona', 'zona']]
    
    if _.shape[0] == 0:
        
        _row = {i:'ND' for i in _.columns}
        _ = _.append(_row, ignore_index=True)
        
    return _

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

# %% QUERY

annuncio = pd.read_sql(f'select * from annuncio where data_prima_presenza_online>"{date_par}"', cnx)
dettaglio = pd.read_sql(f'select * from dettaglio where url_id in (select url_id from annuncio where data_prima_presenza_online>"{date_par}")', cnx)
reversegeo = pd.read_sql(f'select * from reversegecodingad where url_id in (select url_id from annuncio where data_prima_presenza_online>"{date_par}")', cnx)

merge_dataset = pd.merge(annuncio, dettaglio, on='url_id', suffixes=('_ann', '_dett'))
merge_dataset = pd.merge(merge_dataset, reversegeo, on='url_id', suffixes=('', '_rga'))

cnx.close()
# %% Selezione colonne e creazione target

merge_dataset['euro_mq'] = merge_dataset['prezzo'] / merge_dataset['superficie']
bologna_appartamento = merge_dataset.loc[(merge_dataset.comune_rga =='Bologna') & (merge_dataset.tipo_immobile =='Appartamento') & (merge_dataset.affitto == 0)]

col_mask = ['id_ann', 'url_ann', 'data_prima_presenza_online', 'data_ultima_presenza_online', 'latitudine', 
            'longitudine', 'tipo_proprietà', 'prezzo', 'spese_condominio', 'posto_auto', 'ascensore', 'spese_condominio',
            'superficie', 'piano', 'piani_totali', 'locali', 'climatizzato', 'bagni', 'altre_caratteristiche', 
            'anno_costruzione', 'stato', 'riscaldamento', 'climatizzazione','classe_energetica', 'kwh', 'agenzia', 'euro_mq']

bologna_appartamento_masked = bologna_appartamento.loc[:, col_mask]
bologna_appartamento_masked['piani_totali'] = bologna_appartamento_masked.piani_totali.fillna(-1) 

# %% Normalizzazione delle variabili
# %% Tipo propietà
#tipo_prop_map = {i:i.replace('|', ',').split(',')[0] for i in bologna_appartamento_masked.tipo_proprietà.unique()}
#bologna_appartamento_masked['tipo_proprieta_lkp'] = bologna_appartamento_masked.tipo_proprietà.map(tipo_prop_map)

tipo_prop_dict = bologna_appartamento_masked.tipo_proprietà.apply(lambda x: {i.strip().lower():1 for i in x.replace('|', ',').split(',')}).to_dict()
tipo_prop_exploded = pd.DataFrame(tipo_prop_dict).T.fillna(0)
bologna_appartamento_masked = bologna_appartamento_masked.join(tipo_prop_exploded)


# %% Piano
piano_map = {i:i.split(' ')[0] for i in bologna_appartamento_masked['piano'].unique()}
piano_map = {i:it.rjust(2,' ') if it.lower()>='a' else it.zfill(2) if it.zfill(2)<='10' else '10+' for i, it in piano_map.items()}
bologna_appartamento_masked['piano_lkp'] = bologna_appartamento_masked.piano.map(piano_map)

# %% Piani totali
#piani_tot_map = {i:str(int(i)).zfill(2) if i <=10 else '10+'for i in bologna_appartamento_masked['piani_totali'].unique()}
piani_tot_map = {i:str(int(i)).zfill(2) if i <=5 else '5+'for i in bologna_appartamento_masked['piani_totali'].unique()}
bologna_appartamento_masked['piani_totali_lkp'] = bologna_appartamento_masked.piani_totali.map(piani_tot_map)

# %% Locali
bologna_appartamento_masked['locali_lkp'] = bologna_appartamento_masked.locali.fillna('##').apply(lambda x: x.zfill(2))

# %% Bagni
bologna_appartamento_masked['bagni_lkp'] = bologna_appartamento_masked.bagni.fillna('##').apply(lambda x: x.zfill(2))

# %% Altre caratteristiche
altre_caratteristiche_dict = bologna_appartamento_masked.altre_caratteristiche.apply(lambda x: {i.strip().lower():1 for i in x.split('|')}).to_dict()
altre_caratteristiche_exploded = pd.DataFrame(altre_caratteristiche_dict).T.fillna(0)
altre_caratteristiche_exploded.columns = [i+'_ac_feat' for i in altre_caratteristiche_exploded.columns]
bologna_appartamento_masked = bologna_appartamento_masked.join(altre_caratteristiche_exploded)

# %% Riscaldamento
riscaldamento_dict = bologna_appartamento_masked.riscaldamento.apply(lambda x: {'riscaldamento_'+i.strip().lower():1 for i in x.split(',')}).to_dict()
riscaldamento_exploded = pd.DataFrame(riscaldamento_dict).T.fillna(0)#.pipe(clean_names)
bologna_appartamento_masked = bologna_appartamento_masked.join(riscaldamento_exploded)

bologna_appartamento_masked = bologna_appartamento_masked.join(
    pd.DataFrame(bologna_appartamento_masked.riscaldamento.apply(normalize_riscaldamento).to_list(), index=bologna_appartamento_masked.index))

# %% Climatizzatore
climatizzazione_dict = bologna_appartamento_masked.climatizzazione.apply(lambda x: {'climatizzazione_'+i.strip().lower():1 for i in x.split(',')}).to_dict()
climatizzazione_exploded = pd.DataFrame(climatizzazione_dict).T.fillna(0)#.pipe(clean_names)
bologna_appartamento_masked = bologna_appartamento_masked.join(climatizzazione_exploded)

# %% Classe energetica
classe_energetica_map = {i:i.rjust(1,' ')[0] for i in bologna_appartamento_masked.classe_energetica.to_list()}
bologna_appartamento_masked['classe_energetica_lkp'] = bologna_appartamento_masked.classe_energetica.map(classe_energetica_map)


# %% Anno costruzione
bologna_appartamento_masked['anno_costruzione_lkp'] = bologna_appartamento_masked.anno_costruzione.apply(normalize_year)

# %% Arricchisco con informazioni geografiche

bologna_appartamento_masked['P'] = bologna_appartamento_masked[['longitudine', 'latitudine']].apply(lambda x: Point(x['longitudine'], x['latitudine']), axis=1)

geo_enr = bologna_appartamento_masked.P.apply(lambda x: get_geo_info(x,bologna_shp)).to_list()
geo_enr_pdf = pd.concat(geo_enr)
geo_enr_pdf.index = bologna_appartamento_masked.index

bologna_appartamento_masked = bologna_appartamento_masked.join(geo_enr_pdf)

# %%
bologna_appartamento_masked.to_excel('output_data_1k.xlsx')