with data as ( 	
	select distinct  	 	
	d.iddata, 	 	
	d.idcampania, 	 	
	d.idexplotacion, 	 	
	d.idlote, 	 	
	d.idcultivo, 	 	
	d.prod_esperada, 	 	
	d.prod_final,
	l.geom
	from campaign.data d  	 	
	join agrae.lotes l on l.idlote = d.idlote
	where d.idcampania = {} and idexplotacion = {}),
reticula_base as (select rb.*, round((st_area(st_transform(rb.geom,8857)) / 10000)::numeric,2) area from agrae.reticula_base rb join data d on d.idlote = rb.idlote),
rindes as (select dr.volumen,dr.humedad,r.*,dr.geom,d.idlote from field.data_rindes dr
join data d on d.idcampania = dr.idcampania and d.idexplotacion = d.idexplotacion and d.geom && dr.geom
join monitor.rindes r on r.iddata = d.iddata and r.idpoi = dr.id
),
rindes_grid as ( select 
	rb.idlote,
	-- (percentile_cont(0.5) within group (order by r.volumen) * rb.area) as rinde_bruto,
	-- (percentile_cont(0.5) within group (order by r.humedad)) as humedad,
	-- (percentile_cont(0.5) within group (order by r.ajuste) * rb.area) as ajuste,
	-- (percentile_cont(0.5) within group (order by r.rinde) * rb.area) as rinde,
	-- (percentile_cont(0.5) within group (order by r.biomasa) * rb.area) as biomasa,
	-- (percentile_cont(0.5) within group (order by r.residuo) * rb.area) as residuo,
	-- (percentile_cont(0.5) within group (order by r.ms_cosecha) * rb.area) as ms_cosecha,
	-- (percentile_cont(0.5) within group (order by r.ms_residuo) * rb.area) as ms_residuo,
	-- (percentile_cont(0.5) within group (order by r.n_extraido) * rb.area) as n_extraido,
	-- (percentile_cont(0.5) within group (order by r.p_extraido) * rb.area) as p_extraido,
	-- (percentile_cont(0.5) within group (order by r.k_extraido) * rb.area) as k_extraido,
	(percentile_cont(0.5) within group (order by r.volumen)) as rinde_bruto,
	(percentile_cont(0.5) within group (order by r.humedad)) as humedad,
	(percentile_cont(0.5) within group (order by r.ajuste)) as ajuste,
	(percentile_cont(0.5) within group (order by r.rinde)) as rinde,
	(percentile_cont(0.5) within group (order by r.biomasa)) as biomasa,
	(percentile_cont(0.5) within group (order by r.residuo)) as residuo,
	(percentile_cont(0.5) within group (order by r.ms_cosecha)) as ms_cosecha,
	(percentile_cont(0.5) within group (order by r.ms_residuo)) as ms_residuo,
	(percentile_cont(0.5) within group (order by r.n_extraido)) as n_extraido,
	(percentile_cont(0.5) within group (order by r.p_extraido)) as p_extraido,
	(percentile_cont(0.5) within group (order by r.k_extraido)) as k_extraido,
	st_asText(rb.geom) as geom 
	from rindes r
join reticula_base rb on r.idlote = rb.idlote and st_contains(rb.geom, r.geom) 
group by rb.geom, rb.area,rb.idlote)
select r.* from  rindes_grid r