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
	where d.idcampania = {} and d.idexplotacion = {}), -- REQUIERE EL ID DE LA CAMPANIA Y DE LA EXPLOTACION
lotes as (select l.*, 
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
segmentos as (select distinct s.*, l.idlote, l.iddata, l.regimen from agrae.segmentos s join lotes l on st_contains(st_buffer(CAST(l.geom AS geography),4)::geometry,s.geometria)),
segm_analitica as (select 
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
    a.metodo AS p_metodo,
        CASE
            WHEN a.metodo = 1 THEN ( SELECT DISTINCT p.tipo
               FROM analytic.fosforo p
              WHERE p.metodo = a.metodo AND p.regimen = s.regimen AND p.suelo = txt.grupo AND a.p >= p.limite_inferior AND a.p < p.limite_superior)
            WHEN a.metodo = 2 THEN ( SELECT DISTINCT p.tipo
               FROM analytic.fosforo p
              WHERE p.metodo = a.metodo AND p.regimen = s.regimen AND a.p >= p.limite_inferior AND a.p <= p.limite_superior)
            ELSE NULL::character varying
        END AS p_tipo,
        CASE
            WHEN a.metodo = 1 THEN ( SELECT DISTINCT p.incremento
               FROM analytic.fosforo p
              WHERE p.metodo = a.metodo AND p.regimen = s.regimen AND p.suelo = txt.grupo AND a.p >= p.limite_inferior AND a.p < p.limite_superior)
            WHEN a.metodo = 2 THEN ( SELECT DISTINCT p.incremento
               FROM analytic.fosforo p
              WHERE p.metodo = a.metodo AND p.regimen = s.regimen AND a.p >= p.limite_inferior AND a.p <= p.limite_superior)
            ELSE NULL::double precision
        END AS p_inc,
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
	s.geometria as geom
	FROM segmentos s 
	JOIN lotes d  on  s.iddata = d.iddata
	JOIN field.muestras m on m.idcampania = d.idcampania and m.idexplotacion = d.idexplotacion and m.idlote = d.idlote and m.idsegmento = s.idsegmento --join MUESTRAS
	JOIN analytic.analitica a on m.codigo = a.cod
	JOIN analytic.ph ph ON a.ph > ph.limite_inferior AND a.ph <= ph.limite_superior
	JOIN analytic.textura txt ON a.arena >= txt.arena_i AND a.arena <= txt.arena_s AND a.arcilla >= txt.arcilla_i AND a.arcilla <= txt.arcilla_s AND a.ceap >= txt.ceap_i AND a.ceap <= txt.ceap_s
	JOIN analytic.conductividad_electrica ce ON a.ce >= ce.limite_i AND a.ce <= ce.limite_s
	JOIN analytic.carbonatos carb ON (a.carbon / 100::double precision) >= carb.limite_inferior AND (a.carbon / 100::double precision) < carb.limite_superior
	JOIN analytic.caliza_activa ca_ac ON a.caliza >= ca_ac.limite_i AND a.caliza <= ca_ac.limite_s
	JOIN analytic.calcio ca ON ca.suelo = txt.grupo AND a.ca >= ca.limite_inferior AND a.ca <= ca.limite_superior
	JOIN analytic.magnesio mg ON mg.suelo = txt.grupo AND a.mg >= mg.limite_inferior AND a.mg <= mg.limite_superior
	JOIN analytic.cic cic ON a.cic >= cic.limite_i AND a.cic <= cic.limite_s
	JOIN analytic.nitrogeno n ON a.n >= n.limite_inferior AND a.n <= n.limite_superior
	JOIN analytic.potasio k ON k.regimen = s.regimen AND k.suelo = txt.grupo AND a.k >= k.limite_inferior AND a.k < k.limite_superior
	JOIN analytic.sodio na ON na.suelo = txt.grupo AND a.na >= na.limite_inferior AND a.na <= na.limite_superior
	)
{} --QUERY DE LA SELECCION