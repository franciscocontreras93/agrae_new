with data as (select iddata,idcampania,c.nombre as campania,idexplotacion,e.nombre as explotacion,idlote,upper(l.nombre) lote,l.geom from campaign.data d
join campaign.campanias c on c.id = d.idcampania
join agrae.explotacion e using(idexplotacion)
join agrae.lotes l using(idlote)
where d.idcampania = {} and d.idexplotacion = {}),
muestras as (select 
	d.iddata,
	d.campania,
	d.explotacion,
	d.lote,
	m.codigo,
	cp.nombre as prioridad,
	cs.status as status_mues,
	(case
		when a.idanalitica is not null
		then 'PROCESADO'
		else 'PENDIENTE'
	end
	) status_lab,
    st_asText(m.geom) as geom
    from field.muestras m
join data d using (idcampania,idexplotacion,idlote)
join correlations.status cs on cs.id = m.status
join correlations.prioridad cp on cp.id = m.prioridad
left join analytic.analitica a on a.cod = m.codigo
order by d.lote)
{}