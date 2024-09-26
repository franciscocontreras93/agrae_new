with data as (select distinct 
	d.iddata,
	d.idcampania,
	d.idexplotacion,
	ex.nombre as explotacion,
	d.idlote,
	d.idcultivo,
	c.nombre as cultivo,
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
	left join agrae.cultivo c on c.idcultivo = d.idcultivo
	join agrae.explotacion ex on d.idexplotacion = ex.idexplotacion
	where d.idcampania = {} and d.idexplotacion = {} ),
lotes as (select l.idlote, l.nombre, st_transform(st_buffer(st_transform(l.geom,8857),-0.5),4326) as geom,
	d.iddata,
	d.idcampania,
	d.idexplotacion,
	d.idcultivo,
	d.explotacion,
	d.cultivo,
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
segmentos as (select distinct 
s.idsegmento,
s.ceap,
s.segmento,
st_intersection(s.geometria,l.geom) as geometria,
--st_collectionextract(st_union(st_multi(st_intersection(s.geometria,l.geom)),3)) as geometria,
--st_area(st_transform(st_multi(st_intersection(s.geometria,l.geom)),8857)) area,
l.idlote, 
l.iddata, 
l.regimen 
from agrae.segmentos s 
join lotes l on st_intersects(st_buffer(CAST(l.geom AS geography),0)::geometry,s.geometria)
group by s.idsegmento,s.ceap,s.segmento,l.idlote,l.iddata,l.regimen,l.geom), --TESTEAR BUFFER DE EL LOTE
segm_analitica as (select distinct
	m.codigo,
	d.idlote,
	d.nombre,
	s.idsegmento,
	s.segmento,
	txt.grupo_label suelo,
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
	ph.tipo ph_tipo,
	a.ce,
	ce.tipo ce_tipo,
	ce.influencia ce_influencia,
	a.carbon AS carbonatos,
    carb.tipo AS carb_tipo,
    a.ca,
    ca.tipo AS ca_tipo,
    a.mg,
    mg.tipo AS mg_tipo,
    a.caliza * 100::double precision AS caliza,
    ca_ac.tipo AS caliza_tipo,
 	round(a.cic::numeric,3) cic,
 	cic.tipo AS cic_tipo,
 	CASE
            WHEN txt.grupo = 1 AND a.cic = 10::double precision THEN 'Se trata de un suelo del Grupo I, y el CCC, respecto al contenido de arcillas se encuentra en lo recomendable; 10 meq/100g suelo'::text
            WHEN txt.grupo = 2 AND a.cic = 15::double precision THEN 'Se trata de un suelo del Grupo II, y el CCC, respecto al contenido de arcillas se encuentra en lo recomendable; 15 meq/100g suelo'::text
            WHEN txt.grupo = 3 AND a.cic = 20::double precision THEN 'Se trata de un suelo del Grupo III, y el CCC, respecto al contenido de arcillas se encuentra en lo recomendable; 20 meq/100g suelo'::text
            WHEN txt.grupo IS NULL AND a.cic IS NULL THEN NULL::text
            ELSE 'No cumple con los limites recomendados'::text
    END AS cic_caso,
    a.na,
    na.tipo as na_tipo,
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
	FROM segmentos s 
	JOIN lotes d  on  s.iddata = d.iddata
	left JOIN field.muestras m on m.idcampania = d.idcampania and m.idexplotacion = d.idexplotacion and m.idlote = d.idlote and st_intersects(m.geom,s.geometria) --join MUESTRAS
	left JOIN analytic.analitica a on m.codigo = a.cod
	LEFT JOIN analytic.ph ph ON a.ph >= ph.limite_inferior AND a.ph < ph.limite_superior
	LEFT JOIN analytic.textura txt ON  a.ceap >= txt.ceap_i AND a.ceap < txt.ceap_s
	LEFT JOIN analytic.conductividad_electrica ce ON a.ce >= ce.limite_i AND a.ce < ce.limite_s
	LEFT JOIN analytic.carbonatos carb ON (a.carbon / 100::double precision) >= carb.limite_inferior AND (a.carbon / 100::double precision) < carb.limite_superior
	LEFT JOIN analytic.caliza_activa ca_ac ON a.caliza >= ca_ac.limite_i AND a.caliza < ca_ac.limite_s
	LEFT JOIN analytic.calcio ca ON ca.suelo = txt.grupo AND a.ca >= ca.limite_inferior AND a.ca < ca.limite_superior
	LEFT JOIN analytic.magnesio mg ON mg.suelo = txt.grupo AND a.mg >= mg.limite_inferior AND a.mg < mg.limite_superior
	LEFT JOIN analytic.cic cic ON a.cic >= cic.limite_i AND a.cic < cic.limite_s
	LEFT JOIN analytic.nitrogeno n ON a.n >= n.limite_inferior AND a.n < n.limite_superior and n.textura = txt.grupo
	LEFT JOIN analytic.potasio k ON k.textura = txt.grupo AND a.k >= k.limite_inferior AND a.k < k.limite_superior
	LEFT JOIN analytic.sodio na ON na.suelo = txt.grupo AND a.na >= na.limite_inferior AND a.na < na.limite_superior
    LEFT JOIN analytic.fosforo_nuevo p_n on p_n.metodo = a.metodo AND p_n.textura = txt.grupo and p_n.carbonatos = carb.nivel AND a.p >= p_n.limite_inferior AND a.p < p_n.limite_superior
	LEFT JOIN analytic.p_metodos met on a.metodo = met.id
    where not st_isEmpty(s.geometria)),
--ambientes as (select distinct a.idambiente,a.ambiente,a.ndvimax,a.geometria, l.prod_esperada, l.idlote, l.iddata from agrae.ambiente a join lotes l on st_contains(st_buffer(CAST(l.geom AS geography),4)::geometry,a.geometria)),
ambientes as (select distinct a.idambiente,a.ambiente,a.ndvimax,st_collectionextract(st_multi(st_intersection(l.geom,a.geometria)),3) as geometria, l.prod_esperada, l.idlote, l.iddata from agrae.ambiente a join lotes l on st_intersects(l.geom,a.geometria)),
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
	where st_area(a.geometria) > 0
	),	
uf as (select 
	a.idlote,
	a.iddata,
	a.ambiente + s.segmento uf,
	a.ambiente,
	a.ndvimax,
	s.segmento,
	s.ceap,
	s.codigo,
	a.prod_esperada, 
	a.prod_ponderada,
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
	st_multi(st_union(st_multi(ST_CollectionExtract(st_intersection(a.geometria,s.geometria),3)))) as geom
	from extracciones a 
	join segm_analitica s on st_intersects(s.geometria , a.geometria)
	group by a.idlote, a.ambiente, s.segmento, a.iddata
	,a.prod_esperada, a.prod_ponderada,s.codigo,s.ceap,a.ndvimax
	),
necesidades_i as (select --NECESIDADES 1RA APLICACION
uf.idlote, uf.iddata, uf.uf, uf.uf_etiqueta,
	(case -- NECESIDAD N_I
            WHEN q.fertilizantefondoformula IS NULL OR q.fertilizantefondoformula = ''::text THEN uf.necesidad_n
            ELSE uf.necesidad_n - round(
            CASE
                WHEN q.fertilizantefondoajustado::text ~~* 'n'::text THEN round(uf.necesidad_n * 0.20 / ((string_to_array(q.fertilizantefondoformula, '-'::text))[1]::double precision / 100::double precision))
                WHEN q.fertilizantefondoajustado::text ~~* 'p'::text THEN round(uf.necesidad_p / ((string_to_array(q.fertilizantefondoformula, '-'::text))[2]::double precision / 100::double precision))
                WHEN q.fertilizantefondoajustado::text ~~* 'k'::text THEN round(uf.necesidad_k / ((string_to_array(q.fertilizantefondoformula, '-'::text))[3]::double precision / 100::double precision))
                WHEN q.fertilizantefondoajustado::text ~~* 'pk'::text THEN round((uf.necesidad_p / ((string_to_array(q.fertilizantefondoformula, '-'::text))[2]::double precision / 100::double precision) + uf.necesidad_k / ((string_to_array(q.fertilizantefondoformula, '-'::text))[3]::double precision / 100::double precision)) / 2::double precision)
                ELSE NULL::double precision
            END * ((string_to_array(q.fertilizantefondoformula, '-'::text))[1]::double precision / 100::double precision))
     end) AS necesidad_ni ,
     (case -- NECESIDAD P_I
            WHEN q.fertilizantefondoformula IS NULL OR q.fertilizantefondoformula = ''::text THEN uf.necesidad_p
            ELSE uf.necesidad_p - round(
            CASE
                WHEN q.fertilizantefondoajustado::text ~~* 'n'::text THEN round(uf.necesidad_n * 0.20 / ((string_to_array(q.fertilizantefondoformula, '-'::text))[1]::double precision / 100::double precision))
                WHEN q.fertilizantefondoajustado::text ~~* 'p'::text THEN uf.necesidad_p / ((string_to_array(q.fertilizantefondoformula, '-'::text))[2]::double precision / 100::double precision)
                WHEN q.fertilizantefondoajustado::text ~~* 'k'::text THEN round(uf.necesidad_k / ((string_to_array(q.fertilizantefondoformula, '-'::text))[3]::double precision / 100::double precision))
                WHEN q.fertilizantefondoajustado::text ~~* 'pk'::text THEN round((uf.necesidad_p / ((string_to_array(q.fertilizantefondoformula, '-'::text))[2]::double precision / 100::double precision) + uf.necesidad_k / ((string_to_array(q.fertilizantefondoformula, '-'::text))[3]::double precision / 100::double precision)) / 2::double precision)
                ELSE NULL::double precision
            END * ((string_to_array(q.fertilizantefondoformula, '-'::text))[2]::double precision / 100::double precision))
     end) AS necesidad_pi,
     (case -- NECESIDAD K_I
            WHEN q.fertilizantefondoformula IS NULL OR q.fertilizantefondoformula = ''::text THEN uf.necesidad_k
            ELSE uf.necesidad_k - round(
            CASE
                WHEN q.fertilizantefondoajustado::text ~~* 'n'::text THEN round(uf.necesidad_n * 0.20 / ((string_to_array(q.fertilizantefondoformula, '-'::text))[1]::double precision / 100::double precision))
                WHEN q.fertilizantefondoajustado::text ~~* 'p'::text THEN uf.necesidad_p / ((string_to_array(q.fertilizantefondoformula, '-'::text))[2]::double precision / 100::double precision)
                WHEN q.fertilizantefondoajustado::text ~~* 'k'::text THEN round(uf.necesidad_k / ((string_to_array(q.fertilizantefondoformula, '-'::text))[3]::double precision / 100::double precision))
                WHEN q.fertilizantefondoajustado::text ~~* 'pk'::text THEN round((uf.necesidad_p / ((string_to_array(q.fertilizantefondoformula, '-'::text))[2]::double precision / 100::double precision) + uf.necesidad_k / ((string_to_array(q.fertilizantefondoformula, '-'::text))[3]::double precision / 100::double precision)) / 2::double precision)
                ELSE NULL::double precision
            END * ((string_to_array(q.fertilizantefondoformula, '-'::text))[3]::double precision / 100::double precision))
     end) AS necesidad_ki
     from uf join data  q on uf.iddata = q.iddata where not st_isEmpty(uf.geom)),
necesidades_ii as (select --NECESIDADES 2DA APLICACION
uf.idlote, uf.iddata, uf.uf, uf.uf_etiqueta,
(case -- NECESIDAD N_II
            WHEN q.fertilizantecob1formula IS NULL OR q.fertilizantecob1formula = ''::text THEN uf.necesidad_ni
            ELSE uf.necesidad_ni - round(
            CASE
                WHEN q.fertilizantecob1ajustado::text ~~* 'n'::text THEN round(uf.necesidad_ni * 0.50 / ((string_to_array(q.fertilizantecob1formula, '-'::text))[1]::double precision / 100::double precision))
                WHEN q.fertilizantecob1ajustado::text ~~* 'p'::text THEN round(uf.necesidad_pi / ((string_to_array(q.fertilizantecob1formula, '-'::text))[2]::double precision / 100::double precision))
                WHEN q.fertilizantecob1ajustado::text ~~* 'k'::text THEN round(uf.necesidad_ki / ((string_to_array(q.fertilizantecob1formula, '-'::text))[3]::double precision / 100::double precision))
                WHEN q.fertilizantecob1ajustado::text ~~* 'pk'::text THEN round((uf.necesidad_pi / ((string_to_array(q.fertilizantecob1formula, '-'::text))[2]::double precision / 100::double precision) + uf.necesidad_ki / ((string_to_array(q.fertilizantecob1formula, '-'::text))[3]::double precision / 100::double precision)) / 2::double precision)
                ELSE NULL::double precision
            END * ((string_to_array(q.fertilizantecob1formula, '-'::text))[1]::double precision / 100::double precision))
     end) AS necesidad_nii,
     (case -- NECESIDAD P_II
            WHEN q.fertilizantecob1formula IS NULL OR q.fertilizantecob1formula = ''::text THEN uf.necesidad_pi
            ELSE uf.necesidad_pi - round(
            CASE
                WHEN q.fertilizantecob1ajustado::text ~~* 'n'::text THEN round(uf.necesidad_ni * 0.50 / ((string_to_array(q.fertilizantecob1formula, '-'::text))[1]::double precision / 100::double precision))
                WHEN q.fertilizantecob1ajustado::text ~~* 'p'::text THEN round(uf.necesidad_pi / ((string_to_array(q.fertilizantecob1formula, '-'::text))[2]::double precision / 100::double precision))
                WHEN q.fertilizantecob1ajustado::text ~~* 'k'::text THEN round(uf.necesidad_ki / ((string_to_array(q.fertilizantecob1formula, '-'::text))[3]::double precision / 100::double precision))
                WHEN q.fertilizantecob1ajustado::text ~~* 'pk'::text THEN round((uf.necesidad_pi / ((string_to_array(q.fertilizantecob1formula, '-'::text))[2]::double precision / 100::double precision) + uf.necesidad_ki / ((string_to_array(q.fertilizantecob1formula, '-'::text))[3]::double precision / 100::double precision)) / 2::double precision)
                ELSE NULL::double precision
            END * ((string_to_array(q.fertilizantecob1formula, '-'::text))[2]::double precision / 100::double precision))
     end) AS necesidad_pii,
     (case -- NECESIDAD K_II
            WHEN q.fertilizantecob1formula IS NULL OR q.fertilizantecob1formula = ''::text THEN uf.necesidad_ki
            ELSE uf.necesidad_ki - round(
            CASE
                WHEN q.fertilizantecob1ajustado::text ~~* 'n'::text THEN round(uf.necesidad_ni * 0.50 / ((string_to_array(q.fertilizantecob1formula, '-'::text))[1]::double precision / 100::double precision))
                WHEN q.fertilizantecob1ajustado::text ~~* 'p'::text THEN round(uf.necesidad_pi / ((string_to_array(q.fertilizantecob1formula, '-'::text))[2]::double precision / 100::double precision))
                WHEN q.fertilizantecob1ajustado::text ~~* 'k'::text THEN round(uf.necesidad_ki / ((string_to_array(q.fertilizantecob1formula, '-'::text))[3]::double precision / 100::double precision))
                WHEN q.fertilizantecob1ajustado::text ~~* 'pk'::text THEN round((uf.necesidad_pi / ((string_to_array(q.fertilizantecob1formula, '-'::text))[2]::double precision / 100::double precision) + uf.necesidad_ki / ((string_to_array(q.fertilizantecob1formula, '-'::text))[3]::double precision / 100::double precision)) / 2::double precision)
                ELSE NULL::double precision
            END * ((string_to_array(q.fertilizantecob1formula, '-'::text))[3]::double precision / 100::double precision))
     end) AS necesidad_kii
from necesidades_i uf 
join data q on uf.iddata = q.iddata),
necesidades_iii as (select --NECESIDADES 3RA APLICACION
uf.idlote, uf.iddata, uf.uf, uf.uf_etiqueta,
(case -- NECESIDAD N_III
            WHEN q.fertilizantecob2formula IS NULL OR q.fertilizantecob2formula = ''::text THEN uf.necesidad_nii
            ELSE uf.necesidad_nii - round(
            CASE
                WHEN q.fertilizantecob2ajustado::text ~~* 'n'::text THEN round(uf.necesidad_nii * 1 / ((string_to_array(q.fertilizantecob2formula, '-'::text))[1]::double precision / 100::double precision))
                WHEN q.fertilizantecob2ajustado::text ~~* 'p'::text THEN round(uf.necesidad_pii / ((string_to_array(q.fertilizantecob2formula, '-'::text))[2]::double precision / 100::double precision))
                WHEN q.fertilizantecob2ajustado::text ~~* 'k'::text THEN round(uf.necesidad_kii / ((string_to_array(q.fertilizantecob2formula, '-'::text))[3]::double precision / 100::double precision))
                WHEN q.fertilizantecob2ajustado::text ~~* 'pk'::text THEN round((uf.necesidad_pii / ((string_to_array(q.fertilizantecob2formula, '-'::text))[2]::double precision / 100::double precision) + uf.necesidad_kii / ((string_to_array(q.fertilizantecob2formula, '-'::text))[3]::double precision / 100::double precision)) / 2::double precision)
                ELSE NULL::double precision
            END * ((string_to_array(q.fertilizantecob2formula, '-'::text))[1]::double precision / 100::double precision))
     end) AS necesidad_niii,
     (case -- NECESIDAD P_III
            WHEN q.fertilizantecob2formula IS NULL OR q.fertilizantecob2formula = ''::text THEN uf.necesidad_pii
            ELSE uf.necesidad_pii - round(
            CASE
                WHEN q.fertilizantecob2ajustado::text ~~* 'n'::text THEN round(uf.necesidad_nii * 1/ ((string_to_array(q.fertilizantecob2formula, '-'::text))[1]::double precision / 100::double precision))
                WHEN q.fertilizantecob2ajustado::text ~~* 'p'::text THEN round(uf.necesidad_pii / ((string_to_array(q.fertilizantecob2formula, '-'::text))[2]::double precision / 100::double precision))
                WHEN q.fertilizantecob2ajustado::text ~~* 'k'::text THEN round(uf.necesidad_kii / ((string_to_array(q.fertilizantecob2formula, '-'::text))[3]::double precision / 100::double precision))
                WHEN q.fertilizantecob2ajustado::text ~~* 'pk'::text THEN round((uf.necesidad_pii / ((string_to_array(q.fertilizantecob2formula, '-'::text))[2]::double precision / 100::double precision) + uf.necesidad_kii / ((string_to_array(q.fertilizantecob2formula, '-'::text))[3]::double precision / 100::double precision)) / 2::double precision)
                ELSE NULL::double precision
            END * ((string_to_array(q.fertilizantecob2formula, '-'::text))[2]::double precision / 100::double precision))
     end) AS necesidad_piii,
     (case -- NECESIDAD K_III
            WHEN q.fertilizantecob2formula IS NULL OR q.fertilizantecob2formula = ''::text THEN uf.necesidad_kii
            ELSE uf.necesidad_kii - round(
            CASE
                WHEN q.fertilizantecob2ajustado::text ~~* 'n'::text THEN round(uf.necesidad_nii * 1 / ((string_to_array(q.fertilizantecob2formula, '-'::text))[1]::double precision / 100::double precision))
                WHEN q.fertilizantecob2ajustado::text ~~* 'p'::text THEN round(uf.necesidad_pii / ((string_to_array(q.fertilizantecob2formula, '-'::text))[2]::double precision / 100::double precision))
                WHEN q.fertilizantecob2ajustado::text ~~* 'k'::text THEN round(uf.necesidad_kii / ((string_to_array(q.fertilizantecob2formula, '-'::text))[3]::double precision / 100::double precision))
                WHEN q.fertilizantecob2ajustado::text ~~* 'pk'::text THEN round((uf.necesidad_pii / ((string_to_array(q.fertilizantecob2formula, '-'::text))[2]::double precision / 100::double precision) + uf.necesidad_kii / ((string_to_array(q.fertilizantecob2formula, '-'::text))[3]::double precision / 100::double precision)) / 2::double precision)
                ELSE NULL::double precision
            END * ((string_to_array(q.fertilizantecob2formula, '-'::text))[3]::double precision / 100::double precision))
     end) AS necesidad_kiii
from necesidades_ii uf 
join data q on uf.iddata = q.iddata),
necesidades_f as (select --NECESIDADES 4TA APLICACION
uf.idlote, uf.iddata, uf.uf, uf.uf_etiqueta,
(case -- NECESIDAD N_IV
            WHEN q.fertilizantecob3formula IS NULL OR q.fertilizantecob3formula = ''::text THEN uf.necesidad_niii
            ELSE uf.necesidad_niii - round(
            CASE
                WHEN q.fertilizantecob3ajustado::text ~~* 'n'::text THEN round(uf.necesidad_niii * 1 / ((string_to_array(q.fertilizantecob3formula, '-'::text))[1]::double precision / 100::double precision))
                WHEN q.fertilizantecob3ajustado::text ~~* 'p'::text THEN round(uf.necesidad_piii / ((string_to_array(q.fertilizantecob3formula, '-'::text))[2]::double precision / 100::double precision))
                WHEN q.fertilizantecob3ajustado::text ~~* 'k'::text THEN round(uf.necesidad_kiii / ((string_to_array(q.fertilizantecob3formula, '-'::text))[3]::double precision / 100::double precision))
                WHEN q.fertilizantecob3ajustado::text ~~* 'pk'::text THEN round((uf.necesidad_piii / ((string_to_array(q.fertilizantecob3formula, '-'::text))[2]::double precision / 100::double precision) + uf.necesidad_kiii / ((string_to_array(q.fertilizantecob3formula, '-'::text))[3]::double precision / 100::double precision)) / 2::double precision)
                ELSE NULL::double precision
            END * ((string_to_array(q.fertilizantecob3formula, '-'::text))[1]::double precision / 100::double precision))
     end) AS necesidad_nf,
     (case -- NECESIDAD P_IV
            WHEN q.fertilizantecob3formula IS NULL OR q.fertilizantecob3formula = ''::text THEN uf.necesidad_piii
            ELSE uf.necesidad_piii - round(
            CASE
                WHEN q.fertilizantecob3ajustado::text ~~* 'n'::text THEN round(uf.necesidad_niii * 1 / ((string_to_array(q.fertilizantecob3formula, '-'::text))[1]::double precision / 100::double precision))
                WHEN q.fertilizantecob3ajustado::text ~~* 'p'::text THEN round(uf.necesidad_piii / ((string_to_array(q.fertilizantecob3formula, '-'::text))[2]::double precision / 100::double precision))
                WHEN q.fertilizantecob3ajustado::text ~~* 'k'::text THEN round(uf.necesidad_kiii / ((string_to_array(q.fertilizantecob3formula, '-'::text))[3]::double precision / 100::double precision))
                WHEN q.fertilizantecob3ajustado::text ~~* 'pk'::text THEN round((uf.necesidad_piii / ((string_to_array(q.fertilizantecob3formula, '-'::text))[2]::double precision / 100::double precision) + uf.necesidad_kiii / ((string_to_array(q.fertilizantecob3formula, '-'::text))[3]::double precision / 100::double precision)) / 2::double precision)
                ELSE NULL::double precision
            END * ((string_to_array(q.fertilizantecob3formula, '-'::text))[2]::double precision / 100::double precision))
     end) AS necesidad_pf,
     (case -- NECESIDAD K_IV
            WHEN q.fertilizantecob3formula IS NULL OR q.fertilizantecob3formula = ''::text THEN uf.necesidad_kiii
            ELSE uf.necesidad_kiii - round(
            CASE
                WHEN q.fertilizantecob3ajustado::text ~~* 'n'::text THEN round(uf.necesidad_niii * 1 / ((string_to_array(q.fertilizantecob3formula, '-'::text))[1]::double precision / 100::double precision))
                WHEN q.fertilizantecob3ajustado::text ~~* 'p'::text THEN round(uf.necesidad_piii / ((string_to_array(q.fertilizantecob3formula, '-'::text))[2]::double precision / 100::double precision))
                WHEN q.fertilizantecob3ajustado::text ~~* 'k'::text THEN round(uf.necesidad_kiii / ((string_to_array(q.fertilizantecob3formula, '-'::text))[3]::double precision / 100::double precision))
                WHEN q.fertilizantecob3ajustado::text ~~* 'pk'::text THEN round((uf.necesidad_piii / ((string_to_array(q.fertilizantecob3formula, '-'::text))[2]::double precision / 100::double precision) + uf.necesidad_kiii / ((string_to_array(q.fertilizantecob3formula, '-'::text))[3]::double precision / 100::double precision)) / 2::double precision)
                ELSE NULL::double precision
            END * ((string_to_array(q.fertilizantecob3formula, '-'::text))[3]::double precision / 100::double precision))
     end) AS necesidad_kf
from necesidades_iii uf 
join data q on uf.iddata = q.iddata),
necesidades as (select * from uf 
join necesidades_i ni using(idlote, iddata, uf, uf_etiqueta)
join necesidades_ii nii using(idlote, iddata, uf, uf_etiqueta)
join necesidades_iii niii using(idlote, iddata, uf, uf_etiqueta)
join necesidades_f nf using(idlote, iddata, uf, uf_etiqueta)
--join data d using (iddata)
),
aportes as (
select
n.idlote, n.iddata, n.codigo,n.ambiente,n.ndvimax,n.segmento,n.ceap,n.uf, n.uf_etiqueta,
concat(lpad(n.necesidad_n::varchar,4,'0'),'-',lpad(n.necesidad_p::varchar,4,'0'),'-',lpad(n.necesidad_k::varchar,4,'0')) necesidades_iniciales,
coalesce('F'||d.fertilizantefondoformula,'Sin Informacion') fertilizantefondoformula,
	(CASE
            WHEN d.fertilizantefondoajustado::text ~~* 'n'::text AND n.necesidad_n > 0::double precision THEN round((n.necesidad_n) / NULLIF((string_to_array(d.fertilizantefondoformula, '-'::text))[1]::double precision / 100::double precision, 0::double precision))
            WHEN d.fertilizantefondoajustado::text ~~* 'p'::text AND n.necesidad_p > 0::double precision THEN round(n.necesidad_p / NULLIF((string_to_array(d.fertilizantefondoformula, '-'::text))[2]::double precision / 100::double precision, 0::double precision))
            WHEN d.fertilizantefondoajustado::text ~~* 'k'::text AND n.necesidad_k > 0::double precision THEN round(n.necesidad_k / NULLIF((string_to_array(d.fertilizantefondoformula, '-'::text))[3]::double precision / 100::double precision, 0::double precision))
            WHEN d.fertilizantefondoajustado::text ~~* 'pk'::text AND n.necesidad_p > 0::double precision OR n.necesidad_k > 0::double precision THEN round((n.necesidad_p / NULLIF((string_to_array(d.fertilizantefondoformula, '-'::text))[2]::double precision / 100::double precision, 0::double precision) + n.necesidad_k / NULLIF((string_to_array(d.fertilizantefondoformula, '-'::text))[3]::double precision / 100::double precision, 0::double precision)) / 2::double precision)
            ELSE 0::double precision
        end) AS fertilizantefondocalculado,
coalesce('F'||d.fertilizantecob1formula,'Sin Informacion') fertilizantecob1formula,
(CASE
            WHEN d.fertilizantecob1ajustado::text ~~* 'n'::text AND n.necesidad_ni > 0::double precision THEN round(n.necesidad_ni / NULLIF((string_to_array(d.fertilizantecob1formula, '-'::text))[1]::double precision / 100::double precision, 0::double precision))
            WHEN d.fertilizantecob1ajustado::text ~~* 'p'::text AND n.necesidad_pi > 0::double precision THEN round(n.necesidad_pi / NULLIF((string_to_array(d.fertilizantecob1formula, '-'::text))[2]::double precision / 100::double precision, 0::double precision))
            WHEN d.fertilizantecob1ajustado::text ~~* 'k'::text AND n.necesidad_ki > 0::double precision THEN round(n.necesidad_ki / NULLIF((string_to_array(d.fertilizantecob1formula, '-'::text))[3]::double precision / 100::double precision, 0::double precision))
            WHEN d.fertilizantecob1ajustado::text ~~* 'pk'::text AND n.necesidad_pi > 0::double precision OR n.necesidad_ki > 0::double precision THEN round((n.necesidad_pi / NULLIF((string_to_array(d.fertilizantecob1formula, '-'::text))[2]::double precision / 100::double precision, 0::double precision) + n.necesidad_ki / NULLIF((string_to_array(d.fertilizantecob1formula, '-'::text))[3]::double precision / 100::double precision, 0::double precision)) / 2::double precision)
            ELSE 0::double precision
        end) AS fertilizantecob1calculado,
coalesce('F'||d.fertilizantecob2formula,'Sin Informacion') fertilizantecob2formula,
(CASE
            WHEN d.fertilizantecob2ajustado::text ~~* 'n'::text AND n.necesidad_nii > 0::double precision THEN round(n.necesidad_nii / NULLIF((string_to_array(d.fertilizantecob2formula, '-'::text))[1]::double precision / 100::double precision, 0::double precision))
            WHEN d.fertilizantecob2ajustado::text ~~* 'p'::text AND n.necesidad_pii > 0::double precision THEN round(n.necesidad_pii / NULLIF((string_to_array(d.fertilizantecob2formula, '-'::text))[2]::double precision / 100::double precision, 0::double precision))
            WHEN d.fertilizantecob2ajustado::text ~~* 'k'::text AND n.necesidad_kii > 0::double precision THEN round(n.necesidad_kii / NULLIF((string_to_array(d.fertilizantecob2formula, '-'::text))[3]::double precision / 100::double precision, 0::double precision))
            WHEN d.fertilizantecob2ajustado::text ~~* 'pk'::text AND n.necesidad_pii > 0::double precision OR n.necesidad_kii > 0::double precision THEN round((n.necesidad_pii / NULLIF((string_to_array(d.fertilizantecob2formula, '-'::text))[2]::double precision / 100::double precision, 0::double precision) + n.necesidad_kii / NULLIF((string_to_array(d.fertilizantecob2formula, '-'::text))[3]::double precision / 100::double precision, 0::double precision)) / 2::double precision)
            ELSE 0::double precision
        end) AS fertilizantecob2calculado,
coalesce('F'||d.fertilizantecob3formula,'Sin Informacion') fertilizantecob3formula,
(CASE
            WHEN d.fertilizantecob3ajustado::text ~~* 'n'::text AND n.necesidad_niii > 0::double precision THEN round(n.necesidad_niii / NULLIF((string_to_array(d.fertilizantecob3formula, '-'::text))[1]::double precision / 100::double precision, 0::double precision))
            WHEN d.fertilizantecob3ajustado::text ~~* 'p'::text AND n.necesidad_piii > 0::double precision THEN round(n.necesidad_piii / NULLIF((string_to_array(d.fertilizantecob3formula, '-'::text))[2]::double precision / 100::double precision, 0::double precision))
            WHEN d.fertilizantecob3ajustado::text ~~* 'k'::text AND n.necesidad_kiii > 0::double precision THEN round(n.necesidad_kiii / NULLIF((string_to_array(d.fertilizantecob3formula, '-'::text))[3]::double precision / 100::double precision, 0::double precision))
            WHEN d.fertilizantecob3ajustado::text ~~* 'pk'::text AND n.necesidad_piii > 0::double precision OR n.necesidad_kiii > 0::double precision THEN round((n.necesidad_piii / NULLIF((string_to_array(d.fertilizantecob3formula, '-'::text))[2]::double precision / 100::double precision, 0::double precision) + n.necesidad_kiii / NULLIF((string_to_array(d.fertilizantecob3formula, '-'::text))[3]::double precision / 100::double precision, 0::double precision)) / 2::double precision)
            ELSE 0::double precision
        end) AS fertilizantecob3calculado,
concat(lpad(n.necesidad_nf::varchar,4,'0'),'-',lpad(n.necesidad_pf::varchar,4,'0'),'-',lpad(n.necesidad_kf::varchar,4,'0')) necesidades_finales, n.geom
from necesidades n
join data d using (iddata)
),
uf_final as (select 
l.explotacion,
l.cultivo,
l.prod_esperada,
l.nombre as lote,
l.iddata,
a.codigo,
a.uf, 
a.uf_etiqueta,
a.ambiente,
a.ndvimax,
a.segmento,
a.ceap,
a.necesidades_iniciales,
a.necesidades_finales, 
a.fertilizantefondoformula, 
a.fertilizantefondocalculado,
a.fertilizantecob1formula, 
a.fertilizantecob1calculado,
a.fertilizantecob2formula, 
a.fertilizantecob2calculado,
a.fertilizantecob3formula, 
a.fertilizantecob3calculado,
st_union(a.geom) as geom
from aportes a
join lotes l on a.idlote = l.idlote
where  round((st_area(st_transform(st_setsrid(a.geom,4326),8857)) / 10000)::numeric,2) > 0
group by 
l.iddata,
l.nombre,
l.explotacion,
l.cultivo,
l.prod_esperada,
a.codigo,
a.ambiente,
a.ndvimax,
a.segmento,
a.ceap,
a.uf,
a.uf_etiqueta, 
a.necesidades_iniciales,
a.necesidades_finales, 
a.fertilizantefondoformula, 
a.fertilizantefondocalculado,
a.fertilizantecob1formula, 
a.fertilizantecob1calculado,
a.fertilizantecob2formula, 
a.fertilizantecob2calculado,
a.fertilizantecob3formula, 
a.fertilizantecob3calculado,
a.necesidades_finales),
fert_intraparcelaria as (
select distinct
uf.iddata,
uf.explotacion,
uf.lote,
uf.cultivo,
uf.prod_esperada,
uf.codigo,
uf.ambiente,
uf.ndvimax::numeric,
uf.segmento,
uf.ceap,
uf.uf, 
uf.uf_etiqueta, 
uf.necesidades_iniciales,
uf.necesidades_finales,
uf.fertilizantefondoformula as f_fondo, 
uf.fertilizantefondocalculado as d_fondo,
uf.fertilizantecob1formula as f_cob1, 
uf.fertilizantecob1calculado as d_cob1,
uf.fertilizantecob2formula as f_cob2, 
uf.fertilizantecob2calculado as d_cob2,
uf.fertilizantecob3formula as  f_cob3, 
uf.fertilizantecob3calculado as d_cob3,
round((st_area(st_transform(uf.geom,8857)) / 10000)::numeric,2)::double precision area_ha,
uf.geom
from uf_final uf),
fert_report as (select 
	uf.iddata,
	uf.explotacion,
	uf.lote,
	uf.cultivo,
	uf.prod_esperada,
	uf.codigo,
	uf.ambiente,
	uf.ndvimax::numeric,
	uf.segmento,
	uf.ceap,
	uf.uf, 
	uf.uf_etiqueta, 
	uf.necesidades_iniciales,
	uf.necesidades_finales,
	uf.f_fondo,
	uf.d_fondo,
	uf.f_cob1,
	uf.d_cob1,
	uf.f_cob2,
	uf.d_cob2,
	uf.f_cob3,
	uf.d_cob3,
	round(uf.area_ha::numeric,2)::numeric area_ha,
	s.suelo,
	s.n,
	s.n_tipo,
	s.n_inc,
	s.p,
	s.p_tipo,
	s.p_inc,
	s.k,
	s.k_tipo,
	s.k_inc,
	s.ph,
	s.ph_tipo,
	s.ce,
	s.ce_tipo,
	s.ce_influencia,
	s.carbonatos,
	s.carb_tipo,
	s.caliza,
	s.caliza_tipo,
	s.cic::numeric,
	s.cic_tipo,
	s.cic_caso,
	s.na,
	s.arcilla,
	s.limo,
	s.arena,
	s.ca_f,
	s.mg_f,
	s.k_f,
	s.na_f,
	s.al,
	s.b,
	s.fe,
	s.mn,
	s.cu,
	s.zn,
	s.s,
	s.mo,
	s.ni,
	s.co,
	s.ti,
	s."as",
	s.pb,
	s.cr,
	s.organi,
	s.cox,
	s.rel_cn,
	s.ca_eq,
	s.mg_eq,
	s.k_eq,
	s.na_eq
from fert_intraparcelaria uf
join  segm_analitica s on uf.codigo = s.codigo),
fert_parcelaria as (select 
iddata,
lote,
f_fondo,
round(sum(d_fondo) / sum(area_ha)) d_fondo,
f_cob1,
round(sum(d_cob1) / sum(area_ha)) d_cob1,
f_cob2,
round(sum(d_cob2) / sum(area_ha)) d_cob2,
f_cob3,
round(sum(d_cob3) / sum(area_ha)) d_cob3,
sum(area_ha) area_ha,
st_asText(st_union(geom)) as geom
from fert_intraparcelaria
group by iddata,lote,f_fondo,f_cob1,f_cob2,f_cob3),
mapa_sig as (select distinct row_number() over () as id,fp.*,st_asText(fi.geom) as geom from fert_intraparcelaria  fi join fert_report fp on fp.codigo = fi.codigo and fp.uf = fi.uf)
--select * from mapa_sig
{}