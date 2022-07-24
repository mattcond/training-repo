library(data.table)
library(dplyr)
library(lubridate)
library(stringr)
library(dtplyr)

pop_2015 <- fread('popolazione_italia_2015')

mort_ita <- fread('comuni_giornaliero_dati_fino_31agosto.csv.gz', 
                     encoding = 'Latin-1', 
                     na.strings = 'n.d.') %>% 
  select(REG:M_15,F_15,T_15)

mort_ita_set <- mort_ita %>% 
  mutate(GE = str_pad(GE, 4, 'left', '0')) %>% 
  mutate(GE = ymd(paste0('1999', GE))) %>% 
  mutate(
    mese = GE %>% month(),
    week = GE %>% isoweek()) #%>% 
  #select(-GE)




