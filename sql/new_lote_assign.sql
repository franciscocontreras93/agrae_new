with lote as (
	select 
     {} as idcampania, 
	 {} as idexplotacion ,
	'{}' as nombre ,
	nullif('{}','') as cultivo,
	nullif('{}%','') as regimen,
    {}::double precision as produccion,
	st_geomfromtext('{}',4326) as geom
),
union_data as (
	select l.nombre,l.idcampania, l.idexplotacion, c.idcultivo, rg.id as idregimen, l.produccion, st_multi(geom) as geom from lote l
	left join (select * from agrae.cultivo limit 1) as  c on c.nombre ilike l.cultivo
	left join (select * from analytic.regimen limit 1) as rg on rg.nombre ilike l.regimen
	group by l.nombre,l.idcampania, l.idexplotacion, c.idcultivo, rg.id,l.produccion,l.geom
),
new_lote as (
	insert into agrae.lotes(nombre,geom)
	select nombre,geom from union_data 
	returning idlote
)
insert into campaign.data (idcampania,idexplotacion,idlote,idcultivo,idregimen,prod_esperada)
select idcampania, idexplotacion,(select idlote from new_lote),idcultivo,idregimen,produccion
from union_data
returning iddata