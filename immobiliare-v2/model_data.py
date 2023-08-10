#%%
import pandas as pd
import numpy as np
#%%

data = pd.read_excel('PREPROCESSING_STEP1.xlsx', 'Sheet1')

#%%

kpi_500 = pd.read_excel('model/perc_anno_mese.xlsx', 'BOL_KPI_500')
kpi_1000 = pd.read_excel('model/perc_anno_mese.xlsx', 'BOL_KPI_1000')
indice_frag = pd.read_excel('model/dati_esterni/indici-di-fragilita-dal-2021.xlsx')
scaled_euro_mq = pd.read_excel('model/perc_anno_mese.xlsx', 'SCALED_PAR')

#%%

data['aprox_lat'] = data['latitudine'] - data['latitudine'] % 0.005
data['aprox_lng'] = data['longitudine'] - data['longitudine'] % 0.005
data['coord'] = (data['aprox_lat'] * 1000).astype(int).astype(str) +'_'+ (data['aprox_lng'] * 1000).astype(int).astype(str)

#%%

data['aprox_lat_1000'] = data['latitudine'] - data['latitudine'] % 0.01
data['aprox_lng_1000'] = data['longitudine'] - data['longitudine'] % 0.01
data['coord_1000'] = (data['aprox_lat_1000'] * 1000).astype(int).astype(str) +'_'+ (data['aprox_lng_1000'] * 1000).astype(int).astype(str)
data['anno_mese_annuncio'] = data['data_prima_presenza_online'].apply(lambda x: x[:7])

#%%

data = pd.merge(data, kpi_500[['coord', 'N_FERMATE_500','N_FERMATE_CORE_500','N_GIARDINI_500','N_PARCHI_500','N_FARMACIE_500', 'MUSEI_GALLERIE_TEATRI_500']], 
                how='left', on='coord')

data = pd.merge(data, kpi_1000[['coord', 'N_FERMATE_1000','N_FERMATE_CORE_1000','N_GIARDINI_1000','N_PARCHI_1000','N_FARMACIE_1000', 'MUSEI_GALLERIE_TEATRI_1000']], 
                how='left', left_on='coord_1000', right_on='coord')

data = pd.merge(data, scaled_euro_mq[['anno_mese','perc_perimetro']], 
                how='left', left_on='anno_mese_annuncio', right_on='anno_mese')

#%%

piazza_maggiore_coord = [44.49367, 11.34305]
stazione_centrale_coord = [44.50537, 11.34331]

#%%
i_frag_col = ['Cod Area Statistica',
         'Indice potenziale fragilità economica' ,
         'Indice potenziale fragilità sociale' ,
         'Indice potenziale fragilità demografica', 
         'Reddito pro capite mediano delle famiglie', 
         '% ricambio popolaz. straniera tra 20 e 64 anni', 
         '% abitazioni occupate in affitto']
indice_frag = indice_frag[i_frag_col]

indice_frag.columns = ['codice_area_statistica',
         'frag_econ_index',
         'frag_socio_index', 
         'frag_demo_index',
         'reddito_pc',
         'perc_ric_str', 
         'perc_aff']
#%%

for r in data.head(5).iterrows():

    _output_dict = {

        'url_annuncio': r[1]['url_ann'],
        'superficie': int(r[1]['superficie']), 
        'prezzo': int(r[1]['prezzo']), 
        'euro_mq': int(r[1]['euro_mq']),
        'perc_perimetro': round(r[1]['perc_perimetro'], 4),
        'scaled_euro_mq' : int(r[1]['euro_mq'] / r[1]['perc_perimetro']), 
        'scaled_prezzo' : int(r[1]['prezzo'] / r[1]['perc_perimetro']),
        'data_prima_presenza_online': r[1]['data_prima_presenza_online'], 
        'anno_mese_annuncio': r[1]['anno_mese_annuncio'], 
        'perimetro': 'X' if (r[1]['euro_mq'] > 1_850 and r[1]['euro_mq'] < 5_000) and (r[1]['prezzo'] > 125_000 and r[1]['prezzo'] < 700_000) and (r[1]['superficie'] > 40 and r[1]['superficie'] < 180) and int(r[1]['locali'][:1]) > 0 else '' ,
        'pred_euro_mq':-1,
        'pred_prezzo':-1,
        'processato':'',

        ### AREA STATISTICA

        'AS_XXI_APRILE':1 if r[1]['area_statistica'] == 'XXI APRILE' else 0,
        'AS_SAN_GIUSEPPE':1 if r[1]['area_statistica'] == 'SAN GIUSEPPE' else 0,
        'AS_VIA_FERRARESE':1 if r[1]['area_statistica'] == 'VIA FERRARESE' else 0,
        'AS_EX_MERCATO_ORTOFRUTTICOLO':1 if r[1]['area_statistica'] == 'EX MERCATO ORTOFRUTTICOLO' else 0,
        'AS_DAGNINI':1 if r[1]['area_statistica'] == 'DAGNINI' else 0,
        'AS_VILLAGGIO_DELLA_BARCA':1 if r[1]['area_statistica'] == 'VILLAGGIO DELLA BARCA' else 0,
        'AS_BITONE':1 if r[1]['area_statistica'] == 'BITONE' else 0,
        'AS_FOSSOLO':1 if r[1]['area_statistica'] == 'FOSSOLO' else 0,
        'AS_VIA_VITTORIO_VENETO':1 if r[1]['area_statistica'] == 'VIA VITTORIO VENETO' else 0,
        'AS_IRNERIO_1':1 if r[1]['area_statistica'] == 'IRNERIO-1' else 0,
        'AS_CASERME_ROSSE':1 if r[1]['area_statistica'] == 'CASERME ROSSE-MANIFATTURA' else 0,
        'AS_CIRENAICA':1 if r[1]['area_statistica'] == 'CIRENAICA' else 0,
        'AS_CHIESANUOVA':1 if r[1]['area_statistica'] == 'CHIESANUOVA' else 0,
        'AS_MENGOLI':1 if r[1]['area_statistica'] == 'MENGOLI' else 0,
        'AS_VIA_TOSCANA':1 if r[1]['area_statistica'] == 'VIA TOSCANA' else 0,
        'AS_ND':1 if r[1]['area_statistica'] is np.nan else 0,
        'AS_IRNERIO_2':1 if r[1]['area_statistica'] == 'IRNERIO-2' else 0,
        'AS_VELODROMO':1 if r[1]['area_statistica'] == 'VELODROMO' else 0,
        'AS_CROCE_DEL_BIACCO':1 if r[1]['area_statistica'] == 'CROCE DEL BIACCO' else 0,
        'AS_SAN_MICHELE_IN_BOSCO':1 if r[1]['area_statistica'] == 'SAN MICHELE IN BOSCO' else 0,
        'AS_MALPIGHI_2':1 if r[1]['area_statistica'] == 'MALPIGHI-2' else 0,
        'AS_AGUCCHI':1 if r[1]['area_statistica'] == 'AGUCCHI' else 0,
        'AS_CAAB':1 if r[1]['area_statistica'] == 'CAAB' else 0,
        'AS_MEZZOFANTI':1 if r[1]['area_statistica'] == 'MEZZOFANTI' else 0,
        'AS_OSSERVANZA':1 if r[1]['area_statistica'] == 'OSSERVANZA' else 0,
        'AS_VIA_DEL_LAVORO':1 if r[1]['area_statistica'] == 'VIA DEL LAVORO' else 0,
        'AS_SAN_SAVINO':1 if r[1]['area_statistica'] == 'SAN SAVINO' else 0,
        'AS_ARCOVEGGIO':1 if r[1]['area_statistica'] == 'ARCOVEGGIO' else 0,
        'AS_MARCONI_2':1 if r[1]['area_statistica'] == 'MARCONI-2' else 0,
        'AS_CAVEDONE':1 if r[1]['area_statistica'] == 'CAVEDONE' else 0,
        'AS_CANALE_DI_RENO':1 if r[1]['area_statistica'] == 'CANALE DI RENO' else 0,
        'AS_GALVANI_2':1 if r[1]['area_statistica'] == 'GALVANI-2' else 0,
        'AS_TRIUMVIRATO_PIETRA':1 if r[1]['area_statistica'] == 'TRIUMVIRATO-PIETRA' else 0,
        'AS_BATTINDARNO':1 if r[1]['area_statistica'] == 'BATTINDARNO' else 0,
        'AS_GUELFA':1 if r[1]['area_statistica'] == 'GUELFA' else 0,
        'AS_CORELLI':1 if r[1]['area_statistica'] == 'CORELLI' else 0,
        'AS_PONTEVECCHIO':1 if r[1]['area_statistica'] == 'PONTEVECCHIO' else 0,
        'AS_STADIO_MELONCELLO':1 if r[1]['area_statistica'] == 'STADIO-MELONCELLO' else 0,
        'AS_VIA_MONDO':1 if r[1]['area_statistica'] == 'VIA MONDO' else 0,
        'AS_MARCONI_1':1 if r[1]['area_statistica'] == 'MARCONI-1' else 0,
        'AS_CROCE_COPERTA':1 if r[1]['area_statistica'] == 'CROCE COPERTA' else 0,
        'AS_CASTELDEBOLE':1 if r[1]['area_statistica'] == 'CASTELDEBOLE' else 0,
        'AS_EMILIA_PONENTE':1 if r[1]['area_statistica'] == 'EMILIA PONENTE' else 0,
        'AS_PIAZZA_DELL_UNITA':1 if r[1]['area_statistica'] == 'PIAZZA DELL\'UNITA\'' else 0,
        'AS_BIRRA':1 if r[1]['area_statistica'] == 'LA BIRRA' else 0,
        'AS_SIEPELUNGA':1 if r[1]['area_statistica'] == 'SIEPELUNGA' else 0,
        'AS_DUCATI_VILLAGGIO_INA':1 if r[1]['area_statistica'] == 'DUCATI-VILLAGGIO INA' else 0,
        'AS_BORGO_CENTRO':1 if r[1]['area_statistica'] == 'BORGO CENTRO' else 0,
        'AS_TIRO_A_SEGNO':1 if r[1]['area_statistica'] == 'TIRO A SEGNO' else 0,
        'AS_SCANDELLARA':1 if r[1]['area_statistica'] == 'SCANDELLARA' else 0,
        'AS_BEVERARA':1 if r[1]['area_statistica'] == 'BEVERARA' else 0,
        'AS_RAVONE':1 if r[1]['area_statistica'] == 'RAVONE' else 0,
        'AS_VIA_LARGA':1 if r[1]['area_statistica'] == 'VIA LARGA' else 0,
        'AS_ROVERI':1 if r[1]['area_statistica'] == 'ROVERI' else 0,
        'AS_MICHELINO':1 if r[1]['area_statistica'] == 'MICHELINO' else 0,
        'AS_SAVENA_ABBANDONATO':1 if r[1]['area_statistica'] == 'SAVENA ABBANDONATO' else 0,
        'AS_PONTE_SAVENA_LA_BASTIA':1 if r[1]['area_statistica'] == 'PONTE SAVENA-LA BASTIA' else 0,
        'AS_MONTE_DONATO':1 if r[1]['area_statistica'] == 'MONTE DONATO' else 0,
        'AS_SAN_DONNINO':1 if r[1]['area_statistica'] == 'SAN DONNINO' else 0,
        'AS_VIA_ARNO':1 if r[1]['area_statistica'] == 'VIA ARNO' else 0,
        'AS_SCALO_RAVONE':1 if r[1]['area_statistica'] == 'SCALO RAVONE' else 0,
        'AS_ZANARDI':1 if r[1]['area_statistica'] == 'ZANARDI' else 0,
        'AS_MALPIGHI_1':1 if r[1]['area_statistica'] == 'MALPIGHI-1' else 0,
        'AS_DUE_MADONNE':1 if r[1]['area_statistica'] == 'DUE MADONNE' else 0,
        'AS_LAZZARETTO':1 if r[1]['area_statistica'] == 'LAZZARETTO' else 0,
        'AS_PADERNO':1 if r[1]['area_statistica'] == 'PADERNO' else 0,
        'AS_AEROPORTO':1 if r[1]['area_statistica'] == 'AEROPORTO' else 0,
        'AS_RIGOSA':1 if r[1]['area_statistica'] == 'RIGOSA' else 0,
        'AS_VIA_DEL_VIVAIO':1 if r[1]['area_statistica'] == 'VIA DEL VIVAIO' else 0,
        'AS_LAVINO_DI_MEZZO':1 if r[1]['area_statistica'] == 'LAVINO DI MEZZO' else 0,
        'AS_PESCAROLA':1 if r[1]['area_statistica'] == 'PESCAROLA' else 0,
        'AS_LAGHETTI_DEL_ROSARIO':1 if r[1]['area_statistica'] == 'LAGHETTI DEL ROSARIO' else 0,
        'AS_LA_DOZZA':1 if r[1]['area_statistica'] == 'LA DOZZA' else 0,
        'AS_GALVANI_1':1 if r[1]['area_statistica'] == 'GALVANI-1' else 0,
        'AS_PRATI_DI_CAPRARA_OSPEDALE_MAGGIORe':1 if r[1]['area_statistica'] == 'PRATI DI CAPRARA-OSPEDALE MAGGIORE' else 0,
        'AS_PILASTRO':1 if r[1]['area_statistica'] == 'PILASTRO' else 0,
        'AS_CADRIANO_CALAMOSCO':1 if r[1]['area_statistica'] == 'CADRIANO-CALAMOSCO' else 0,
        'AS_LUNGO_SAVENA':1 if r[1]['area_statistica'] == 'LUNGO SAVENA' else 0,
        'AS_OSPEDALE_S_ORSOLA':1 if r[1]['area_statistica'] == 'OSPEDALE SANT\'ORSOLA' else 0,
        'AS_STRADELLI_GUELFI':1 if r[1]['area_statistica'] == 'STRADELLI GUELFI' else 0,
        'AS_FIERA':1 if r[1]['area_statistica'] == 'FIERA' else 0,
        'AS_LA_NOCE':1 if r[1]['area_statistica'] == 'LA NOCE' else 0,
        'AS_SAN_LUCA':1 if r[1]['area_statistica'] == 'SAN LUCA' else 0,
        'AS_BARGELLINO':1 if r[1]['area_statistica'] == 'BARGELLINO' else 0,
        'AS_GIARDINI_MARGHERITA':1 if r[1]['area_statistica'] == 'GIARDINI MARGHERITA' else 0,
        'AS_MULINO_DEL_GOMITO':1 if r[1]['area_statistica'] == 'MULINO DEL GOMITO' else 0,


        ### ANNO COSTRUZIONE LKP

        'AC_0_NO_ANNO':1 if r[1]['anno_costruzione_lkp'] == '0_NO_ANNO' else 0,
        'AC_1_ANTE_1950':1 if r[1]['anno_costruzione_lkp'] == '1_ANTE_1950' else 0,
        'AC_2_1950':1 if r[1]['anno_costruzione_lkp'] == '2_1950' else 0,
        'AC_3_1950_1960':1 if r[1]['anno_costruzione_lkp'] == '3_1950_1960' else 0,
        'AC_4_1960_1970':1 if r[1]['anno_costruzione_lkp'] == '4_1960_1970' else 0,
        'AC_5_1970':1 if r[1]['anno_costruzione_lkp'] == '5_1970' else 0,
        'AC_6_1970_1990':1 if r[1]['anno_costruzione_lkp'] == '6_1970_1990' else 0,
        'AC_7_1990_2010':1 if r[1]['anno_costruzione_lkp'] == '7_1990_2010' else 0,
        'AC_8_POST_2010':1 if r[1]['anno_costruzione_lkp'] == '8_POST_2010' else 0,

        ### STATO

        'ST_BUONO':1 if r[1]['stato'] == 'Buono / Abitabile' else 0,
        'ST_DA_RISTRUTTURARE':1 if r[1]['stato'] == 'Da ristrutturare' else 0,
        'ST_NUOVO':1 if r[1]['stato'] == 'Nuovo / In costruzione' else 0,
        'ST_OTTIMO':1 if r[1]['stato'] == 'Ottimo / Ristrutturato' else 0,
        'ST_ND':1 if r[1]['stato'] is np.nan else 0,
        'ST_PARTECIPABILE':1 if r[1]['stato'] == 'Partecipabile' else 0,
        'ST_NON_PARTECIP':1 if r[1]['stato'] == 'Non partecipabile' else 0,

        ### BAGNI

        'BA_01_02':1 if r[1]['bagni_lkp'] in ['01', '02'] else 0,
        'BA_GT_03':1 if r[1]['bagni_lkp'] in ['03', '3+'] else 0,
        'BA_#':1 if r[1]['bagni_lkp'] not in ['01', '02', '03', '3+'] else 0,

        ### CLIMAT

        'CLIMATIZZATO':1 if r[1]['climatizzato'] == 1 else 0,

        ### PIANI TOTALI

        'PT_#':1 if r[1]['piani_totali_lkp'] == '-1' else 0,
        'PT_01_05':1 if r[1]['piani_totali_lkp'] in ['01', '02', '03', '04', '05'] else 0,
        'PT_GT_05':1 if r[1]['piani_totali_lkp'] == '5+' else 0,

        ### N PROPR

        'NUDA_PROPRIETA': r[1]['nuda proprietà'] ,

        ### INT PROPR

        'INTERA_PROPRIETA': r[1]['intera proprietà'] ,

        ### LOCALI

        'LO_01':1 if r[1]['locali_lkp'] == '01' else 0,
        'LO_02':1 if r[1]['locali_lkp'] == '02' else 0,
        'LO_03':1 if r[1]['locali_lkp'] == '03' else 0,
        'LO_4+':1 if r[1]['locali_lkp'] in ['04', '05', '5+'] else 0,
        'LO_##':1 if r[1]['locali_lkp'] not in ['01', '02', '03', '04', '05', '5+'] else 0,

        ### SUPERFICIE MEDIA LOCALI

        'LOCALI_SUP': round(r[1]['superficie'] / int(r[1]['locali'][:1]), 2),

        ### DIST P MAGG

        'DIST_P_MAGG_S1000': round(np.sqrt(np.power((r[1]['latitudine']-piazza_maggiore_coord[0]),2) + 
                               np.power((r[1]['longitudine']-piazza_maggiore_coord[1]),2)
                               )*1000, 2),

        ### DIST S CENT

        'DIST_S_CENT_S1000': round(np.sqrt(np.power((r[1]['latitudine']-stazione_centrale_coord[0]),2) + 
                               np.power((r[1]['longitudine']-stazione_centrale_coord[1]),2)
                               )*1000,2),

        ### ALTRE CARATTERISTICHE

        'AC_CANTINA': r[1]['cantina'],
        'AC_ARREDATO': r[1]['arredato'],
        'AC_CANCELLO': r[1]['cancello'],
        'AC_TAVERNA': r[1]['taverna'],
        'AC_BALCONE': r[1]['balcone'],
        'AC_ARMADIO_A_MURO':r[1]['armadio_a_muro'],
        'AC_ARREDATO':r[1]['arredato'],
        'AC_CAMINETTO':r[1]['caminetto'],
        'AC_CANNA_FUMARIA':r[1]['canna_fumaria'],
        'AC_CUCINA':r[1]['cucina'],
        'AC_ESP_DOPPIA':r[1]['esposizione_doppia'],
        'AC_ESP_ESTERNA':r[1]['esposizione_esterna'],
        'AC_ESP_INTERNA':r[1]['esposizione_interna'],
        'AC_INF_IN_LEGNO':r[1]['infissi_in_legno'],
        'AC_INF_IN_METALLO':r[1]['infissi_in_metallo'],
        'AC_INF_IN_PVC':r[1]['infissi_in_pvc'],

        'AC_GIARDINO':r[1]['giardino'] ,
        'AC_IMPIANTO_TV':r[1]['impianto_tv'] ,
        'AC_PORTIERE':r[1]['portiere'],

        'AC_IDROMASSAGGIO':r[1]['idromassaggio'] ,
        'AC_ALLARME':r[1]['impianto_allarme'],
        'AC_MANSARDA':r[1]['mansarda'] ,
        'AC_PARC_BICI':r[1]['parcheggio_bici'],
        'AC_P_CARRABILE':r[1]['passo_carrabile'] ,

        'AC_PISCINA':r[1]['piscina'] ,
        'AC_P_BLINDATA':r[1]['porta_blindata'] ,
        'AC_VIDEOCITOFONO':r[1]['videocitofono'] ,
        'AC_TERRAZZA':r[1]['terrazza'] ,

        ### ESPOSIZIONE

        'ES_OVEST':r[1]['esposizione_ovest'] ,
        'ES_NORD':r[1]['esposizione_nord'] ,
        'ES_SUD':r[1]['esposizione_sud'] ,
        'ES_EST':r[1]['esposizione_est'] ,

        ### TIPO RISCALDAMENTO

        'RT_RADIATORI':1 if r[1]['riscaldamento_tipo_cat'] == 'a radiatori' else 0,
        'RT_PAVIMENTO':1 if r[1]['riscaldamento_tipo_cat'] == 'a pavimento' else 0,
        'RT_ARIA':1 if r[1]['riscaldamento_tipo_cat'] == 'ad aria' else 0,
        'RT_STUFA':1 if r[1]['riscaldamento_tipo_cat'] == 'a stufa' else 0,
        'RT_ND':1 if r[1]['riscaldamento_tipo_cat'] is np.nan else 0,

        ### ALIMENTAZIONE RISCALDAMENTO

        'RA_METANO':1 if r[1]['riscaldamento_alimentazione_cat'] == 'metano' else 0,
        'RA_GAS':1 if r[1]['riscaldamento_alimentazione_cat'] == 'gas' else 0,
        'RA_TELERISCALDAMENTO':1 if r[1]['riscaldamento_alimentazione_cat'] == 'teleriscaldamento' else 0,
        'RA_GPL':1 if r[1]['riscaldamento_alimentazione_cat'] == 'gpl' else 0,
        'RA_CALORE':1 if r[1]['riscaldamento_alimentazione_cat'] == 'calore' else 0,
        'RA_FOTOVOLTAICO':1 if r[1]['riscaldamento_alimentazione_cat'] == 'fotovoltaico' else 0,
        'RA_ELETTRICA':1 if r[1]['riscaldamento_alimentazione_cat'] == 'elettrica' else 0,
        'RA_GASOLIO':1 if r[1]['riscaldamento_alimentazione_cat'] == 'gasolio' else 0,
        'RA_SOLARE':1 if r[1]['riscaldamento_alimentazione_cat'] == 'solare' else 0,
        'RA_ND':1 if r[1]['riscaldamento_alimentazione_cat'] is np.nan else 0,

        ### KPI BOLOGNA

        'GK_FERMATE':0 if r[1]['N_FERMATE_500'] is np.nan or r[1]['N_FERMATE_500']==0 else 1,
        'GK_FERMATE_CORE':0 if r[1]['N_FERMATE_CORE_500'] is np.nan or r[1]['N_FERMATE_CORE_500']==0 else 1,
        'GK_FARMACIE':0 if r[1]['N_FARMACIE_500'] is np.nan or r[1]['N_FARMACIE_500']==0 else 1,
        'GK_MUSEI':0 if r[1]['MUSEI_GALLERIE_TEATRI_1000'] is np.nan or r[1]['MUSEI_GALLERIE_TEATRI_1000']==0 else 1,
        'GK_PARCHI':0 if (r[1]['N_GIARDINI_500'] is np.nan or r[1]['N_GIARDINI_500']==0) and (r[1]['N_PARCHI_500'] is np.nan or r[1]['N_PARCHI_500']==0) else 1

    }

    print(_output_dict)

#%%

#%%

#%%