with data as (select distinct 
	d.iddata,
	d.idcampania,
	d.idexplotacion,
	d.idlote,
	d.idcultivo, 
	d.idregimen
	from campaign.data d 
	join agrae.cultivo c on c.idcultivo = d.idcultivo
	where d.idcampania = {} and d.idexplotacion = {}), -- REQUIERE EL ID DE LA CAMPANIA Y DE LA EXPLOTACION
lotes as (select l.*, 
	d.iddata,
	d.idcampania,
	d.idexplotacion,
	d.idcultivo,
	d.idregimen as regimen
	from data d join agrae.lotes l on d.idlote = l.idlote ),
ceap as (select c.ceap,c.kf,c.geom as geom from agrae.ceap90 c join lotes l on c.geom && l.geom),
unidos as (select l.idlote,l.nombre as lote, c.ceap, c.kf, st_asText(c.geom) as geom from ceap c join lotes l on st_intersects(l.geom,c.geom))
select * from unidos