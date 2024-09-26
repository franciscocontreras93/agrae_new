with data as (select distinct 
	d.iddata,
	d.idcampania,
	d.idexplotacion,
	d.idlote,
	d.idcultivo, 
	d.idregimen,
	d.fertilizantefondoformula,
	d.fertilizantefondoajustado,
	d.fertilizantecob1formula,
	d.fertilizantecob1ajustado,
	d.fertilizantecob2formula,
	d.fertilizantecob2ajustado,
	d.fertilizantecob3formula,
	d.fertilizantecob3ajustado,
	c.ms_cosecha,
	c.extraccioncosechan,
	c.extraccioncosechap,
	c.extraccioncosechak, 
	c.ms_residuo,
	c.extraccionresiduon,
	c.extraccionresiduop,
	c.extraccionresiduok, 
	d.prod_esperada 
	from campaign.data d 
	join agrae.cultivo c on c.idcultivo = d.idcultivo
	where d.idcampania = {} and d.idexplotacion = {} and d.idlote = {}),
lotes as (select l.idlote, l.nombre, st_transform(st_buffer(st_transform(l.geom,8857),-0.5),4326) as geom, 
	d.iddata,
	d.idcampania,
	d.idexplotacion,
	d.idcultivo,
	d.idregimen as regimen,
	d.ms_cosecha,
	d.extraccioncosechan,
	d.extraccioncosechap,
	d.extraccioncosechak, 
	d.ms_residuo,
	d.extraccionresiduon,
	d.extraccionresiduop,
	d.extraccionresiduok, 
	d.prod_esperada from data d join agrae.lotes l on d.idlote = l.idlote ),	
segmentos as (select distinct s.ceap,
	s.segmento,
	st_multi(st_intersection(s.geometria,l.geom)) as geometria,
	st_area(st_multi(st_intersection(s.geometria,l.geom))) area,
	l.idlote, 
	l.iddata, 
	l.regimen from agrae.segmentos s 
	join lotes l on st_intersects(st_buffer(CAST(l.geom AS geography),4)::geometry,s.geometria)),
segm_analitica as (select 
	m.codigo,
	d.idlote,
	s.segmento,
	txt.grupo_label ||'-' || txt.grupo suelo,
	s.ceap,
	a.n,
    n.tipo AS n_tipo,
    n.incremento AS n_inc,
 	a.p,
    met.nombre AS p_metodo,
    p_n.etiqueta as p_tipo,
    p_n.incremento as p_inc,
    a.k,
    k.tipo AS k_tipo,
    k.incremento AS k_inc,
	a.ph,
	ph.tipo ph,
	a.ce,
	ce.tipo ce_tipo,
	ce.influencia ce_influencia,
	a.carbon AS carbonatos,
    carb.tipo AS carb_tipo,
    a.caliza * 100::double precision AS caliza,
    ca_ac.tipo AS caliza_tipo,
 	round(a.cic::numeric,3) cic,
 	cic.tipo AS cic_tipo,
    a.na,
    a.arcilla,
    a.limo,
    a.arena,
    a.ca_f,
    a.mg_f,
    a.k_f,
    a.na_f,
    a.al,
    a.b,
    a.fe,
    a.mn,
    a.cu,
    a.zn,
    a.s,
    a.mo,
    a.ni,
    a.co,
    a.ti,
    a."as",
    a.pb,
    a.cr,
    a.organi * 100::double precision AS organi,
    a.cox * 100::double precision AS cox,
    a.rel_cn,
    a.ca_eq,
    a.mg_eq,
    a.k_eq,
    a.na_eq,
	s.geometria 
	from segmentos s 
	JOIN campaign.data d  on  s.iddata = d.iddata 
	LEFT JOIN field.muestras m on m.idcampania = d.idcampania and m.idexplotacion = d.idexplotacion and m.idlote = d.idlote and st_intersects(s.geometria,m.geom) --join MUESTRAS
	LEFT JOIN analytic.analitica a on m.codigo = a.cod
	LEFT JOIN analytic.ph ph ON a.ph > ph.limite_inferior AND a.ph <= ph.limite_superior
	LEFT JOIN analytic.textura txt ON a.ceap >= txt.ceap_i and a.ceap < txt.ceap_s
	LEFT JOIN analytic.conductividad_electrica ce ON a.ce >= ce.limite_i AND a.ce < ce.limite_s
	LEFT JOIN analytic.carbonatos carb ON a.carbon >= carb.limite_inferior AND a.carbon < carb.limite_superior
	LEFT JOIN analytic.caliza_activa ca_ac ON a.caliza >= ca_ac.limite_i AND a.caliza <= ca_ac.limite_s
	LEFT JOIN analytic.cic cic ON a.cic >= cic.limite_i AND a.cic <= cic.limite_s
	LEFT JOIN analytic.nitrogeno n ON a.n >= n.limite_inferior AND a.n < n.limite_superior and n.textura = txt.grupo
	LEFT JOIN analytic.potasio k ON k.textura = txt.grupo AND a.k >= k.limite_inferior AND a.k < k.limite_superior
	LEFT JOIN analytic.sodio na ON na.suelo = txt.grupo AND a.na >= na.limite_inferior AND a.na < na.limite_superior
	LEFT JOIN analytic.fosforo_nuevo p_n on p_n.metodo = a.metodo AND p_n.textura = txt.grupo and p_n.carbonatos = carb.nivel AND a.p >= p_n.limite_inferior AND a.p < p_n.limite_superior
	LEFT JOIN analytic.p_metodos met on a.metodo = met.id
	where s.area > 0
	),
--ambientes as (select distinct a.idambiente,a.ambiente,a.ndvimax,a.geometria, l.prod_esperada, l.idlote, l.iddata from agrae.ambiente a join lotes l on st_contains(st_buffer(CAST(l.geom AS geography),4)::geometry,a.geometria)),
ambientes as (select distinct a.idambiente,a.ambiente,a.ndvimax,st_intersection(l.geom,a.geometria) as geometria, l.prod_esperada, l.idlote, l.iddata from agrae.ambiente a join lotes l on st_intersects(l.geom,a.geometria)),
amb_40 as (select distinct a.idlote,avg(a.ndvimax) as ndvimed from ambientes a where a.ambiente = 40 group by a.idlote),
producciones as ( -- CALCULO PRODUCCIONES PONDERADAS
	select a.idambiente,
			a.idlote,
		round( 
		case 	
			when a.ambiente = 40  		
				then a.prod_esperada 
			else		
				avg(a.ndvimax) * a.prod_esperada  / (select avg(ndvimed) from amb_40 where idlote = a.idlote) 	
		  end ) 
		as prod_ponderada 
	from ambientes a
	group by a.idambiente,a.ambiente,a.prod_esperada,a.idlote
	),
amb_join as (select a.*, p.prod_ponderada from ambientes a join producciones p on a.idambiente = p.idambiente and a.idlote = p.idlote),
extracciones as (select
		a.*, -- EXTRACCION COSECHA
		round( -- EXTRACCION N
			d.ms_cosecha * a.prod_ponderada * d.extraccioncosechan
		) as extraccioncosechan,
		round( -- EXTRACCION P
			d.ms_cosecha * a.prod_ponderada * d.extraccioncosechap
		) as extraccioncosechap,
		round( -- EXTRACCION K
			d.ms_cosecha * a.prod_ponderada * d.extraccioncosechak
		) as extraccioncosechak,-- EXTRACCION RESIDUO
		round( -- EXTRACCION N
			d.ms_residuo * a.prod_ponderada * d.extraccionresiduon
		) as extraccionresiduon,
		round( -- EXTRACCION P
			d.ms_residuo * a.prod_ponderada * d.extraccionresiduop
		) as extraccionresiduop,
		round( -- EXTRACCION K
			d.ms_residuo * a.prod_ponderada * d.extraccionresiduok
		) as extraccionresiduok
	from amb_join a
	join data d on d.idlote = a.idlote
	),	
uf as (select 
	a.idlote,
	a.iddata,
	a.ambiente + s.segmento uf,
	a.prod_esperada, 
	a.prod_ponderada,
	a.extraccioncosechan,
	a.extraccioncosechap,
	a.extraccioncosechak,
	a.extraccionresiduon,
	a.extraccionresiduop,
	a.extraccionresiduok,
	CASE
            WHEN (s.segmento + a.ambiente) = 23 THEN 'UF1'::text
            WHEN (s.segmento + a.ambiente) = 43 THEN 'UF2'::text
            WHEN (s.segmento + a.ambiente) = 63 THEN 'UF3'::text
            WHEN (s.segmento + a.ambiente) = 21 THEN 'UF4'::text
            WHEN (s.segmento + a.ambiente) = 41 THEN 'UF5'::text
            WHEN (s.segmento + a.ambiente) = 61 THEN 'UF6'::text
            WHEN (s.segmento + a.ambiente) = 22 THEN 'UF7'::text
            WHEN (s.segmento + a.ambiente) = 42 THEN 'UF8'::text
            WHEN (s.segmento + a.ambiente) = 62 THEN 'UF9'::text
            ELSE NULL::text
        END AS uf_etiqueta,
	round(max((a.extraccioncosechan + a.extraccionresiduon) * (1 + s.n_inc))) necesidad_n,
	round(max((a.extraccioncosechap + a.extraccionresiduop) * (1 + s.p_inc))) necesidad_p,
	round(max((a.extraccioncosechak + a.extraccionresiduok) * (1 + s.k_inc))) necesidad_k,
	st_asText(st_multi(st_union(st_multi(ST_CollectionExtract(st_intersection(a.geometria,s.geometria),3))))) as geom
	from extracciones a 
	join segm_analitica s on st_intersects(s.geometria , a.geometria)
	group by a.idlote, a.ambiente, s.segmento, a.iddata
	,a.prod_esperada, a.prod_ponderada, a.extraccioncosechan,
	a.extraccioncosechap,
	a.extraccioncosechak,
	a.extraccionresiduon,
	a.extraccionresiduop,
	a.extraccionresiduok
	)
select  u.uf_etiqueta, 
        u.prod_ponderada::integer,
        (round(u.extraccioncosechan) || ' / ' ||
        round(u.extraccioncosechap) || ' / ' ||
        round(u.extraccioncosechak)) cos_npk,
        (round(u.extraccionresiduon) || ' / ' ||
        round(u.extraccionresiduop) || ' / ' ||
        round(u.extraccionresiduok)) res_npk, 
        (round(u.necesidad_n) || ' / ' ||
        round(u.necesidad_p) || ' / ' ||
        round(u.necesidad_k)) aportes_npk,
--        round((st_area(u.geom) * 1000000)::numeric,2) area, --AREA ELIPSOIDAL
        round((st_area(st_transform(st_setsrid(u.geom,4326),8857)) / 10000)::numeric,2) area --AREA PLANIMETRICA
        from uf u
		where round((st_area(st_transform(st_setsrid(u.geom,4326),8857)) / 10000)::numeric,2) > 0 and u.uf_etiqueta is not null 
		order by u.uf_etiqueta