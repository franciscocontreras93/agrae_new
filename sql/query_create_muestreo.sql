with data as (
	select 
		idcampania,
		idexplotacion,
		iddata,
		idlote 
	from campaign.data where iddata in ({})),
lotes as (
	select 
	idlote,
	idcampania,
	idexplotacion,
	st_transform(st_buffer(st_transform(geom,8857),-10),4326) geom
	from agrae.lotes 
	join data using (idlote)),
segmentos as (
	select
		idlote,
		idcampania,
		idexplotacion,
		segmento,
		(case 
			when st_isEmpty(st_transform(st_buffer(st_transform(st_intersection(s.geometria,b.geom),8857),-10),4326))
				then st_intersection(s.geometria,b.geom) 
			else st_transform(st_buffer(st_transform(st_intersection(s.geometria,b.geom),8857),-10),4326)
		end) as geom,
		st_area(st_transform(s.geometria,8857)) / 10000 as area
		from agrae.segmentos s 
	join lotes  b on st_intersects(s.geometria,b.geom)
	where segmento in ({})),
grouped as (
	select idlote,
		idcampania,
		idexplotacion,
		segmento,
		st_area(st_transform(st_multi(st_union(geom)),8857)) / 10000 as area,
		st_multi(st_union(geom)) as geom
	from segmentos
	group by idlote,
		idcampania,
		idexplotacion,
		segmento 
	order by idlote,segmento asc ),
muestreo as (select 
		s.idcampania,
		s.idexplotacion,
		s.idlote,
		s.segmento,
	case			
		when s.area <= 2.5 then  st_generatePoints(s.geom,3,50)
		when s.area > 2.5 and s.area <= 5 then  st_generatePoints(s.geom,4,50)
		when s.area > 5 and s.area <= 10 then  st_generatePoints(s.geom,7,50)
		when s.area > 10 and s.area <= 20 then  st_generatePoints(s.geom,14,50)
		when s.area > 20  then  st_generatePoints(s.geom,24,50)		
	end as geom
from grouped s order by idlote, segmento asc),
accion as ( insert into field.muestras (idcampania,idexplotacion,idlote,segmento,geom) 
	select idcampania,idexplotacion,idlote,segmento,geom
	from muestreo returning uid,codigo)
select * from accion