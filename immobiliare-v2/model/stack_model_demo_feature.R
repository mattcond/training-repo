setwd('C:\\Users\\matte\\OneDrive\\Documenti\\Progetti\\training-repo\\immobiliare-v2')

library(openxlsx)
library(dplyr)
library(stringr)
library(randomForest)
library(xgboost)
library(plotly)

dataset <- read.xlsx('output_data_20230717_212837.xlsx', 'Sheet1')
perc_anno <- read.xlsx('model/perc_anno_mese.xlsx', sheet = 'SCALED')
kpi_500 <- read.xlsx('model/perc_anno_mese.xlsx', sheet = 'BOL_KPI_500')
kpi_1000 <- read.xlsx('model/perc_anno_mese.xlsx', sheet = 'BOL_KPI_1000')
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

piazza_maggiore_coord <- c(44.49367, 11.34305)
stazione_centrale_coord <- c(44.50537, 11.34331)

dataset_mod <- 
  dataset %>% 
  filter(
    between(euro_mq, 1850, 5000), 
    between(superficie, 40, 180), 
    between(prezzo, 125000, 700000), 
    !is.na(locali), 
    locali > 0,
    PERIMETRO == 'X'
    
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
    dist_s_cen = sqrt((latitudine-s_cen_lat)^2 + (longitudine-s_cen_lng)^2)*100, 
    aprox_lat = latitudine - latitudine %% 0.005, 
    aprox_lng = longitudine - longitudine %% 0.005, 
    
  ) %>% 
  left_join(perc_anno, by='anno_mese') %>% 
  left_join(indice_frag_sel, by='codice_area_statistica') %>% 
  left_join(kpi_500, by=c('aprox_lat', 'aprox_lng')) %>% 
  left_join(kpi_1000, by=c('aprox_lat', 'aprox_lng')) %>% 
  
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
    cl_feramte = case_when(
      
      is.na(N_FERMATE_500) | N_FERMATE_500 == 0 ~ 0, 
      T~1
      
    ),
    
    cl_feramte_core = case_when(
      
      is.na(N_FERMATE_CORE_500) | N_FERMATE_CORE_500 == 0 ~ 0, 
      T~1
      
    ),
    cl_giardini = ifelse(coalesce(N_GIARDINI_500, 0)+coalesce(N_PARCHI_500, 0)>0, 1, 0),
    cl_farmacie = ifelse(coalesce(N_FARMACIE_500, 0)>0, 1, 0),
    cl_museo = ifelse(coalesce(MUSEI_GALLERIE_TEATRI_1000, 0)>0, 1, 0),
    riscaldamento_tipo_cat = ifelse(is.na(riscaldamento_tipo_cat), 'ND', riscaldamento_tipo_cat), 
    stato = ifelse(is.na(stato), 'ND', stato), 
    riscaldamento_alimentazione_cat = ifelse(is.na(riscaldamento_alimentazione_cat), 'ND', riscaldamento_alimentazione_cat),
    
    
  ) %>% 
  rename(
    nuda_proprieta = nuda.proprietà, 
    intera_proprieta = intera.proprietà)

## DEMO MODEL

mod <- lm(scaled_euro_mq~
                      area_statistica+
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
                      cancello.elettrico_ac_feat+
                      taverna_ac_feat+
                      #balcone+
                      riscaldamento_tipo_cat+
                      riscaldamento_alimentazione_cat+
                      #frag_econ_index+
                      #frag_demo_index+
                      #frag_socio_index+
                      #reddito_pc+
                      cl_feramte+ 
                      cl_feramte_core+
                      cl_giardini+
                      cl_farmacie+
                      cl_museo, 
          data = dataset_mod)

mod %>% summary()
mean(mod$residuals^2) %>% sqrt()
mod$residuals %>% sort %>% plot()

mod$residuals %>% MASS::truehist()

plot(mod)

## FEAT MODEL

rf_model <- randomForest(scaled_euro_mq~
                           area_statistica+
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
                           cancello.elettrico_ac_feat+
                           taverna_ac_feat+
                           #balcone+
                           riscaldamento_tipo_cat+
                           riscaldamento_alimentazione_cat+
                           #frag_econ_index+
                           #frag_demo_index+
                           #frag_socio_index+
                           #reddito_pc+
                           cl_feramte+ 
                           cl_feramte_core+
                           cl_giardini+
                           cl_farmacie+
                           cl_museo,
                         ntree = 50, 
                         mtry=7, 
                         data = dataset_mod)
rf_model
rf_model %>% summary()
rf_model$mse %>% sqrt()
varImpPlot(rf_model)

### PRED

pred <- dataset_mod %>% 
  select(scaled_euro_mq) %>% 
  mutate(
    demo_model = predict(mod), 
    feat_model = predict(rf_model)
  ) #%>% 
  #mutate(scaled_euro_mq_pred = 0.5*demo_model + 0.5*feat_model)

gs <- expand.grid(seq(0,1,0.01), seq(0,1,0.01)) %>% data.frame()
colnames(gs) <- c('mod1', 'mod2')
gs$r_sum = rowSums(gs)
gs <- gs %>% filter(r_sum > 0)
gs$mse <- NA_real_
n_row_gs <- nrow(gs)

for(r in 1:n_row_gs){
  mod1 <- gs[r, 'mod1']
  mod2 <- gs[r, 'mod2']
  rs <- gs[r, 'r_sum']
  
  pred <- pred %>% 
    mutate(scaled_euro_mq_pred = (mod1*demo_model + mod2*feat_model)/rs)
  mse_eval <- mean((pred$scaled_euro_mq - pred$scaled_euro_mq_pred)^2) %>% sqrt
  gs[r, 'mse'] <- mse_eval
  if(mse_eval < 350){
    print(paste(mod1, " - ", mod2,": ", mse_eval))
  }
}

x_mse <- gs %>% pull(mod1) %>% unique() %>% sort
y_mse <- gs %>% pull(mod2) %>% unique() %>% sort
z_mse <- gs %>% arrange(mod1, mod2) %>% pull(mse) %>% matrix(nrow = length(x_mse))

mse_df <- list('x' = x_mse, 'y'=y_mse, 'z'=z_mse)

mse_matrix <- as.matrix(gs[,c('mod1', 'mod2', 'mse')])

kd <- with(MASS::geyser, MASS::kde2d(duration, waiting, n = 50))
fig <- plot_ly(x = mse_df$x, y = mse_df$y, z = mse_df$z) %>% add_surface()

fig



mean((pred$scaled_euro_mq - pred$scaled_euro_mq_pred)^2) %>% sqrt

par(mfrow = c(1, 1))
(pred$scaled_euro_mq - pred$scaled_euro_mq_pred) %>% sort() %>% plot()


par(mfrow = c(2, 2))
plot(pred$demo_model , pred$scaled_euro_mq, xlim = c(0, 5000), ylim = c(0, 5000))
abline(0, 1, col = 'red', lwd=2)

plot(pred$feat_model , pred$scaled_euro_mq, xlim = c(0, 5000), ylim = c(0, 5000))
abline(0, 1, col = 'red', lwd=2)

plot(pred$demo_model , pred$feat_model, xlim = c(0, 5000), ylim = c(0, 5000))
abline(0, 1, col = 'red', lwd=2)

plot(pred$scaled_euro_mq_pred , pred$scaled_euro_mq, xlim = c(0, 5000), ylim = c(0, 5000))
abline(0, 1, col = 'red', lwd=2)

