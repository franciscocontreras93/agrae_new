with data as (select iddata,idlote from campaign.data where iddata in ({})),
lotes as (select d.*, round((st_area(st_transform(l.geom,8857)) / 10000)::numeric,2) area_lote from agrae.lotes l  join data d using(idlote)),
calculo_areas as (select 
    sum(area_lote) suma
    from lotes
    ),
calculo as (select iddata,round(area_lote / (select suma from calculo_areas) * {}) produccion from lotes)
UPDATE campaign."data" d
SET prod_final=src.produccion, rinde_status='Ajustado'::character varying
from calculo as src
WHERE d.iddata = src.iddata;