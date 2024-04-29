with lote as (select '{}' as nombre ,st_geomfromtext('{}',4326) as geom),
validation as (select l.*, lb.idlote from lote l left join agrae.lotes lb on st_equals(lb.geom,l.geom)),
data as (insert into agrae.lotes (nombre,geom) 
		select nombre,geom from validation 
		where idlote is null
		returning nombre)
select * from data
