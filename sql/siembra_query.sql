with data as (select distinct 
	d.iddata,
	d.idcampania,
	d.idexplotacion,
	d.idlote,
	d.idcultivo, 
	d.idregimen
	from campaign.data d 
	left join agrae.cultivo c on c.idcultivo = d.idcultivo
	where d.idcampania = {} and d.idexplotacion = {} and d.idcultivo = {}), -- REQUIERE EL ID DE LA CAMPANIA Y DE LA EXPLOTACION
lotes as (select l.*, 
	d.iddata,
	d.idcampania,
	d.idexplotacion,
	d.idcultivo,
	d.idregimen as regimen
	from data d join agrae.lotes l on d.idlote = l.idlote ),
ceap as (select c.ce36, c.geometria as geom from agrae.ce c join lotes l on c.geometria && l.geom),
unidos as (select l.idlote,l.nombre as lote, c.ce36, st_asText(st_intersection(c.geom,l.geom)) as geom from ceap c join lotes l on st_intersects(l.geom,c.geom))
select * from unidos 