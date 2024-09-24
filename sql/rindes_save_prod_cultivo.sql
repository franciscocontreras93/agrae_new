with data as (select iddata, idlote from campaign.data where idcampania = {} and idexplotacion = {} and idcultivo = {}),
lotes as (select d.*, round((st_area(st_transform(l.geom,8857)) / 10000)::numeric,2) area_lote from agrae.lotes l  join data d using(idlote)),
calculo_areas as (select 
    sum(area_lote) suma
    from lotes
    ),
calculo as (select iddata,round(area_lote / (select suma from calculo_areas) * {}) produccion from lotes)
update campaign.data 
    set prod_final = datos.produccion,
        rinde_status = 'Ajustado'
from calculo as datos
where campaign.data.iddata = datos.iddata::integer