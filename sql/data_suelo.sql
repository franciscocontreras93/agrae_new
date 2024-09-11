with data as (select distinct 
	d.iddata,
	d.idcampania,
	d.idexplotacion,
	d.idlote,
	d.idcultivo, 
	d.idregimen
	from campaign.data d 
	join agrae.cultivo c on c.idcultivo = d.idcultivo
	where d.idcampania = {} and d.idexplotacion = {} and d.idlote = {}),
lotes as (select l.*, 
	d.iddata,
	d.idcampania,
	d.idexplotacion,
	d.idcultivo,
	d.idregimen as regimen
	from data d join agrae.lotes l on d.idlote = l.idlote ),	
segmentos as (select distinct s.ceap,s.segmento,st_multi(st_intersection(s.geometria,l.geom)) as geometria, l.idlote, l.iddata, l.regimen from agrae.segmentos s join lotes l on st_intersects(st_buffer(CAST(l.geom AS geography),4)::geometry,s.geometria)),
segm_analitica as (
	select 
	s.segmento,
    n.tipo AS n_tipo,
    p_n.etiqueta as p_tipo,
    k.tipo AS k_tipo,
    carb.tipo AS carb_tipo
	from segmentos s 
	JOIN campaign.data d  on  s.iddata = d.iddata 
	LEFT JOIN field.muestras m on m.idcampania = d.idcampania and m.idexplotacion = d.idexplotacion and m.idlote = d.idlote and st_intersects(s.geometria,m.geom) --join MUESTRAS
	JOIN analytic.analitica a on m.codigo = a.cod
	JOIN analytic.textura txt ON  a.ceap >= txt.ceap_i AND a.ceap < txt.ceap_s
	JOIN analytic.carbonatos carb ON (a.carbon / 100::double precision) >= carb.limite_inferior AND (a.carbon / 100::double precision) < carb.limite_superior
	LEFT JOIN analytic.nitrogeno n ON a.n >= n.limite_inferior AND a.n < n.limite_superior and n.textura = txt.grupo
	LEFT JOIN analytic.potasio k ON k.textura = txt.grupo AND a.k >= k.limite_inferior AND a.k < k.limite_superior
	LEFT JOIN analytic.fosforo_nuevo p_n on p_n.metodo = a.metodo AND p_n.textura = txt.grupo and p_n.carbonatos = carb.nivel AND a.p >= p_n.limite_inferior AND a.p < p_n.limite_superior
	LEFT JOIN analytic.p_metodos met on a.metodo = met.id
	)
select * from segm_analitica order by segmento