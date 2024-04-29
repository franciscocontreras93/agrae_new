with muestra as (select * from field.muestras where idcampania = {} and idexplotacion = {}),
-- BUSQUEDA DE LAS MUESTRAS QUE YA EXISTAN PARA LA CAMPA;A  Y QUE LA GREGUE AL REPORTE QUE SE GENERA
data as (select m.codigo,idregimen from campaign.data d join muestra m on d.idcampania = m.idcampania and d.idexplotacion = m.idexplotacion and d.idlote = m.idlote),
segmento as (select m.codigo,s.segmento,percentile_cont(0.5) WITHIN GROUP(ORDER BY ce.ce36) ceap from agrae.segmentos s 
			join muestra m on m.idsegmento = s.idsegmento
			join agrae.ce ce on st_intersects(s.geometria,ce.geometria)
			group by m.codigo, s.segmento),
unidos as (
	select m.codigo, d.idregimen, round(s.ceap::numeric,2) ceap
	from muestra m 
	join data d on m.codigo = d.codigo
	join segmento s on m.codigo = s.codigo)
select * from unidos;