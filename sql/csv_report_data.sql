with muestra as (select * from field.muestras where idcampania = 37 and idexplotacion = 1),
-- BUSQUEDA DE LAS MUESTRAS QUE YA EXISTAN PARA LA CAMPA;A  Y QUE LA GREGUE AL REPORTE QUE SE GENERA
data as (select m.codigo,idregimen from campaign.data d join muestra m on d.idcampania = m.idcampania and d.idexplotacion = m.idexplotacion and d.idlote = m.idlote),
segmento as (select m.codigo,s.segmento,percentile_cont(0.5) WITHIN GROUP(ORDER BY ce.ce36) ceap from agrae.segmentos s 
			join muestra m on m.idsegmento = s.idsegmento
			join agrae.ce ce on st_intersects(s.geometria,ce.geometria)
			group by m.codigo, s.segmento),
analisis as (select a.* from muestra m left join analytic.analitica a on m.codigo = a.cod),
unidos as (
	select m.codigo, round(s.ceap::numeric,2) ceap, a.n, a.p,a.k,a.ph,a.ce,a.carbon,a.ca,a.mg,a.na,a.cic,a.ca_eq,a.mg_eq,a.k_eq,a.na_eq,a.ca_f,a.mg_f,a.k_f,a.na_f,a.s,a.mn,a.b,a.mo,a.zn,a.organi,a.cox,a.rel_cn,a.caliza,a.al,a.fe,a.cu,a.arcilla,a.limo,a.arena,a.ni,a.co,a.ti,a."as",a.pb,a.cr,a.metodo
	from muestra m 
	join data d on m.codigo = d.codigo
	join segmento s on m.codigo = s.codigo
	left join analisis a on a.cod = m.codigo
	order by m.codigo)
select * from unidos;