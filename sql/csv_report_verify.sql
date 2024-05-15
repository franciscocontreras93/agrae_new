with data as (select * from campaign.data where idcampania = {} and idexplotacion = {}),
muestras as (select m.* from data d join field.muestras m using (idcampania,idexplotacion,idlote)),
analisis as (select a.*,m.segmento segm from muestras m join analytic.analitica a on a.cod = m.codigo)
select cod,segm,ceap,n,p,k,ph,ce,carbon,ca,mg,na,cic,ca_eq,mg_eq,k_eq,na_eq,ca_f,mg_f,k_f,na_f,s,mn,b,mo,zn,organi,cox,rel_cn,caliza,al,fe,cu,arcilla,limo,arena,ni,co,ti,"as",pb,cr,metodo
from analisis