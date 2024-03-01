with muestra as (select * from field.muestras where idcampania = {} and idexplotacion = {}),
data as (select m.codigo,idregimen from campaign.data d join muestra m on d.idcampania = m.idcampania and d.idexplotacion = m.idexplotacion and d.idlote = m.idlote),
segmento as (select m.codigo,ceap from agrae.segmentos s join muestra m on m.idsegmento = s.idsegmento),
unidos as (
	select m.codigo, d.idregimen, s.ceap
	from muestra m 
	join data d on m.codigo = d.codigo
	join segmento s on m.codigo = s.codigo)
select * from unidos;