setwd('C:\\Users\\matte\\OneDrive\\Documenti\\Progetti\\training-repo\\immobiliare-v2')

library(openxlsx)
library(dplyr)
library(stringr)

dataset <- read.xlsx('output_data_20230717_212837.xlsx')
perc_anno <- read.xlsx('model/perc_anno_mese.xlsx')

indice_frag <- read.xlsx('model/dati_esterni/indici-di-fragilita-dal-2021.xlsx')

indice_frag_sel <- indice_frag %>% 
  select(Cod.Area.Statistica, 
         Indice.potenziale.fragilità.economica, 
         Indice.potenziale.fragilità.sociale, 
         Indice.potenziale.fragilità.demografica, 
         Reddito.pro.capite.mediano.delle.famiglie, 
         `%.ricambio.popolaz..straniera.tra.20.e.64.anni`, 
         `%.abitazioni.occupate.in.affitto`) %>% 
  rename(
    codice_area_statistica = Cod.Area.Statistica,
    frag_econ_index = Indice.potenziale.fragilità.economica, 
    frag_demo_index = Indice.potenziale.fragilità.demografica, 
    frag_socio_index = Indice.potenziale.fragilità.sociale,
    reddito_pc = Reddito.pro.capite.mediano.delle.famiglie, 
    perc_ric_str = `%.ricambio.popolaz..straniera.tra.20.e.64.anni`, 
    perc_aff = `%.abitazioni.occupate.in.affitto`
    
    ) %>% 
  mutate(codice_area_statistica = as.character(codice_area_statistica))
  
  
dataset %>% head()

dataset$euro_mq %>% quantile(probs = seq(0,1,.05), na.rm = T) # 1850 - 5000

dataset$superficie %>% quantile(probs = seq(0,1,.05), na.rm = T) # 1850 - 5000

dataset$prezzo %>% quantile(probs = seq(0,1,.05), na.rm = T) # 1850 - 5000


dataset %>% group_by(tipo_proprieta) %>% summarise(mean(prezzo, na.rm = T), n()) %>% print(n=50)

dataset %>% group_by(anno_costruzione_lkp) %>% summarise(mean(prezzo, na.rm = T), n()) %>% print(n=50)

piazza_maggiore_coord <- c(44.49367, 11.34305)
stazione_centrale_coord <- c(44.50537, 11.34331)

dataset_mod <- 
  dataset %>% 
  filter(
    between(euro_mq, 1850, 5000), 
    between(superficie, 40, 180), 
    between(prezzo, 125000, 700000), 
    !is.na(locali), 
    locali > 0
    
    ) %>%
  mutate(
    
    p_mag_lat = ifelse(T, piazza_maggiore_coord[1], NA),
    p_mag_lng = ifelse(T, piazza_maggiore_coord[2], NA),
    
    s_cen_lat = ifelse(T, stazione_centrale_coord[1], NA),
    s_cen_lng = ifelse(T, stazione_centrale_coord[2], NA),
    
    anno_mese = str_sub(data_prima_presenza_online, 1,7), 
    locali_int = as.integer(str_sub(locali, 1, 1)), 
    locali_sup = superficie / locali_int, 
    dist_p_magg = sqrt((latitudine-p_mag_lat)^2 + (longitudine-p_mag_lng)^2)*100,
    dist_s_cen = sqrt((latitudine-s_cen_lat)^2 + (longitudine-s_cen_lng)^2)*100
    
  ) %>% 
  left_join(perc_anno, by='anno_mese') %>% 
  left_join(indice_frag_sel, by='codice_area_statistica') %>% 
  
  mutate(
    
    frag_econ_index = ifelse(is.na(frag_econ_index), 0, frag_econ_index),
    frag_demo_index = ifelse(is.na(frag_demo_index), 0, frag_demo_index),
    frag_socio_index = ifelse(is.na(frag_socio_index), 0, frag_socio_index),
    reddito_pc = ifelse(is.na(reddito_pc), 0, reddito_pc),
    perc_ric_str = ifelse(is.na(perc_ric_str), 0, perc_ric_str),
    perc_aff = ifelse(is.na(perc_aff), 0, perc_aff),
    
  ) %>% 
  
  mutate(
    scaled_euro_mq = (euro_mq / perc_perimetro), 
    scaled_prezzo = (prezzo / perc_perimetro),
    bagni_lkp_agg = case_when(
      bagni_lkp %in% c('##', '00')  ~ '##',
      bagni_lkp %in% c("01", "02") ~ "01 - 02",
      T ~ '03+'
    ), 
    spese_condominio_adj = case_when(
      spese_condominio %in% c("-1", "") ~ NA_integer_,
      T ~ as.integer(spese_condominio)
    ), 
    locali_lkp_agg = case_when(
      locali_lkp %in% c('##', '00') ~ '##',
      locali_lkp %in% c("01", "02", "03") ~ locali_lkp,
      T ~ "04+"
    ), 
    stato_agg = case_when(
      
      stato %in% c("Nuovo / In costruzione", "Ottimo / Ristrutturato") ~ 'OTTIMO',
      stato == "Buono / Abitabile" ~ 'BUONO',
      stato == "Da ristrutturare" ~ 'DA_RIST',
      stato %in% c("Partecipabile", "Non partecipabile") ~ 'PART', 
      T ~ '#'
      
    ),
    piani_totali_lkp_agg = ifelse(piani_totali_lkp == '5+', 1, 0),
    giardino = giardino.privato_ac_feat+giardino.comune_ac_feat+giardino.privato.e.comune_ac_feat, 
    arredato = arredato_ac_feat + parzialmente.arredato_ac_feat,
    balcone = balcone_ac_feat+`1.balcone_ac_feat`+`2.balconi_ac_feat`+`3.balconi_ac_feat`+`4.balconi_ac_feat`,
    
    cluster_dist_p_mag = case_when(
      
      #dist_p_magg <= .5 ~  '0. 0 - 0,5',
      dist_p_magg <= 1. ~  '1. 0,5 - 1,0',
      dist_p_magg <= 2. ~  '2. 1,0 - 2,0',
      #dist_p_magg <= 3.5 ~  '3. 2,0 - 3,5',
      T ~ '4. > 3,5'
      
    ), 
    
    cluster_dist_s_cen = case_when(
      
      dist_s_cen <= .5 ~  '0. 0 - 0,5',
      dist_s_cen <= 1. ~  '1. 0,5 - 1,0',
      dist_s_cen <= 2. ~  '2. 1,0 - 2,0',
      dist_s_cen <= 3.5 ~  '3. 2,0 - 3,5',
      T ~ '4. > 3,5'
      
    ), 
    riscaldamento_tipo_cat = ifelse(is.na(riscaldamento_tipo_cat), 'ND', riscaldamento_tipo_cat), 
    stato = ifelse(is.na(stato), 'ND', stato), 
    riscaldamento_alimentazione_cat = ifelse(is.na(riscaldamento_alimentazione_cat), 'ND', riscaldamento_alimentazione_cat) 
    
  ) %>% 
  rename(
    nuda_proprieta = nuda.proprietà, 
    intera_proprieta = intera.proprietà)

write.xlsx(dataset_mod, 'dataset_mod.xlsx')

mod <- lm(scaled_euro_mq~
            zona+
            anno_costruzione_lkp+
            stato+
            bagni_lkp_agg+
            climatizzato+
            piani_totali_lkp_agg+
            nuda_proprieta+
            intera_proprieta+
            locali_lkp_agg+
            locali_sup+
            climatizzato+
            dist_p_magg+
            dist_s_cen+
            cantina_ac_feat+
            arredato_ac_feat+
            cancello.elettrico_ac_feat+#taverna_ac_feat+balcone+
            riscaldamento_tipo_cat+
            riscaldamento_alimentazione_cat+
            frag_econ_index+
            frag_demo_index+
            frag_socio_index+
            reddito_pc+
            perc_ric_str, 
          data = dataset_mod)

mod %>% summary()
mean(mod$residuals^2) %>% sqrt()
mod$residuals %>% sort %>% plot()

mod$residuals %>% MASS::truehist()

plot(mod)


dataset %>% 
  filter(!is.na(anno_costruzione), anno_costruzione_lkp != '0_NO_ANNO', anno_costruzione_lkp !=  '1_ANTE_1950') %>% 
  group_by(quartiere, anno_costruzione) %>% 
  summarise(n = n()) %>% 
  arrange(quartiere, desc(n)) %>% 
  ungroup() %>% 
  mutate(anno_costruzione=as.integer(anno_costruzione), 
         anno_costruzione)

forecast <- dataset_mod %>% 
  select(url_ann, anno_mese, data_prima_presenza_online, 
         superficie, prezzo, euro_mq, scaled_euro_mq, perc_perimetro) %>% 
  mutate(
    scaled_euro_mq_forec = mod$fitted.values,
    euro_mq_forec = scaled_euro_mq_forec * perc_perimetro,
    prezzo_forec = euro_mq_forec * superficie, 
    delta_prezzo = prezzo_forec - prezzo
    )





