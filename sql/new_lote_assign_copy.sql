with lote as (select '{}' as nombre ,st_multi(st_force2d(st_geomfromtext('{}',4326))) as geom),
union_data as (select {} as idcampania, {} as idexplotacion, nombre, geom from lote),
new_lote as (
	insert into agrae.lotes(nombre,geom)
	select nombre,geom from union_data 
	returning idlote
)
insert into campaign.data (idcampania,idexplotacion,idlote)
select idcampania, idexplotacion,(select idlote from new_lote)
from union_data
returning iddata