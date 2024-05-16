with values as (select '{}' as cod,
{}::double precision as ceap,
{}::double precision as ph ,
{}::double precision as ce,
{}::double precision carbon,
{}::double precision caliza,
{}::double precision ca,
{}::double precision mg,
{}::double precision k,
{}::double precision na,
{}::double precision n,
{}::double precision p,
{}::double precision organi,
{}::double precision al,
{}::double precision b,
{}::double precision fe,
{}::double precision mn,
{}::double precision cu,
{}::double precision zn,
{}::double precision s ,
{}::double precision mo,
{}::double precision arcilla,
{}::double precision limo,
{}::double precision arena,
{}::double precision ni,
{}::double precision co,
{}::double precision ti,
{}::double precision "as",
{}::double precision pb,
{}::double precision cr,
{} metodo)
INSERT INTO analytic.analitica
(cod,ceap,ph,ce,carbon,caliza,ca,mg,k,na,n,p,organi,al,b,fe,mn,cu,zn,s,mo,arcilla,limo,arena,ni,co,ti,"as",pb,cr,metodo)
SELECT src.cod, src.ceap, src.ph, src.ce, src.carbon, src.caliza, src.ca, src.mg, src.k, src.na, src.n, src.p, src.organi, src.al, src.b, src.fe, src.mn, src.cu, src.zn, src.s, src.mo, src.arcilla, src.limo, src.arena, src.ni, src.co, src.ti, src."as", src.pb, src.cr, src.metodo
FROM values AS src
ON CONFLICT (cod)
DO UPDATE 
SET idanalitica=EXCLUDED.idanalitica, ceap=EXCLUDED.ceap, ph=EXCLUDED.ph, ce=EXCLUDED.ce, carbon=EXCLUDED.carbon, caliza=EXCLUDED.caliza, ca=EXCLUDED.ca, mg=EXCLUDED.mg, k=EXCLUDED.k, na=EXCLUDED.na, n=EXCLUDED.n, p=EXCLUDED.p, organi=EXCLUDED.organi,  al=EXCLUDED.al, b=EXCLUDED.b, fe=EXCLUDED.fe, mn=EXCLUDED.mn, cu=EXCLUDED.cu, zn=EXCLUDED.zn, s=EXCLUDED.s, mo=EXCLUDED.mo, ni=EXCLUDED.ni, co=EXCLUDED.co, ti=EXCLUDED.ti, "as"=EXCLUDED."as", pb=EXCLUDED.pb, cr=EXCLUDED.cr, metodo=EXCLUDED.metodo;