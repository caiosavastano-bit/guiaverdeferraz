/* ---------- Precos unitarios: padrao do orcamento, editaveis e guardados no celular ---------- */
const brl=(v,d=2)=>"R$ "+fmt(v,d);
const numBR=t=>{ t=String(t).trim().replace(/\s/g,""); if(t.includes(",")) t=t.replace(/\./g,"").replace(",","."); const v=parseFloat(t); return isFinite(v)?v:NaN; };
function precosObra(o){ const p={}; if(o&&o.precos) for(const it of o.precos.itens) p[it[0]]=it[3]; return p; }
function precosGuardados(o){ try{ const g=JSON.parse(localStorage.getItem("cotas.precos."+o.id)||"{}"); return g&&typeof g==="object"?g:{} }catch(e){ return {} } }
function precosUso(){ const o=S.obra, p=precosObra(o), g=precosGuardados(o); for(const k in g) if(k in p && typeof g[k]==="number" && isFinite(g[k]) && g[k]>=0) p[k]=g[k]; return p; }
function guardaPreco(id,v){ const o=S.obra, g=precosGuardados(o), pad=precosObra(o)[id]; if(v==null||v===pad) delete g[id]; else g[id]=v; try{ localStorage.setItem("cotas.precos."+o.id,JSON.stringify(g)) }catch(e){} }
function itemPreco(o,id){ return o.precos.itens.find(x=>x[0]===id)||[id,id,"",0]; }
function el(tag,cls,txt){ const e=document.createElement(tag); if(cls) e.className=cls; if(txt!=null) e.textContent=txt; return e; }

/* ---------- Muro de arrimo ---------- */
// Cada muro: eixo em UTM, estaca inicial s0, e colunas de 2 m lidas da vista frontal do projeto: [cota base, cota topo, 8 contagens de pecas Terramesh].
const TPK=["t05x5","t05x6","t05x7","t05x8","t10x5","t10x6","t10x7","t10x8"];
S.mu={A:null,B:null,m:null,res:null};
function preparaMuros(o){
  if(!o.muros||o._mu) return;
  for(const m of o.muros.lista){ let acc=0; m._arc=[0];
    for(let i=1;i<m.eixo.length;i++){ acc+=Math.hypot(m.eixo[i][0]-m.eixo[i-1][0],m.eixo[i][1]-m.eixo[i-1][1]); m._arc.push(acc); }
    m._L=acc; let fT=0,fG=0;
    m._c=m.cols.map(c=>{ const H=c[1]-c[0]; let hT=0,vt=0; for(let k=0;k<8;k++){ const n=c[2+k]; if(!n) continue; hT+=n*(k<4?0.5:1); vt+=n*(k<4?0.5:1)*m.passo; }   // caixa da peca: altura x 1 m x 2 m
      const a=m.passo*hT, b=m.passo*Math.max(0,H-hT); fT+=a; fG+=b; return {base:c[0],top:c[1],H,fT:a,fG:b,vt}; });
    m._fT=fT; m._fG=fG; m._f=fT+fG; }
  o._mu=true;
}
function muroProj(m,E,N){ let bd=1e9, ba=0; const P=m.eixo;
  for(let i=0;i<P.length-1;i++){ const a=P[i], b=P[i+1], vx=b[0]-a[0], vy=b[1]-a[1], L2=vx*vx+vy*vy; let t=L2?((E-a[0])*vx+(N-a[1])*vy)/L2:0; t=Math.max(0,Math.min(1,t));
    const d=Math.hypot(E-(a[0]+t*vx),N-(a[1]+t*vy)); if(d<bd){ bd=d; ba=m._arc[i]+t*Math.sqrt(L2); } }
  return {d:bd, s:m.s0+ba*m.k}; }
function muroPerto(o,E,N){ let b=null; for(const m of o.muros.lista){ const r=muroProj(m,E,N); if(!b||r.d<b.d) b={m,d:r.d,s:r.s}; } return b; }
function muroPonto(m,s){ const a=Math.max(0,Math.min(m._L,(s-m.s0)/m.k)), P=m.eixo; let i=1; while(i<P.length-1&&m._arc[i]<a) i++;
  const l=m._arc[i]-m._arc[i-1], t=l?(a-m._arc[i-1])/l:0; return {E:P[i-1][0]+t*(P[i][0]-P[i-1][0]), N:P[i-1][1]+t*(P[i][1]-P[i-1][1])}; }
function muroColIdx(m,s){ return Math.max(0,Math.min(m._c.length-1,Math.floor((s-m.s0)/m.passo+1e-9))); }
const estaca=s=>{ const v=Math.round(s); return Math.floor(v/100)+"+"+String(v%100).padStart(2,"0"); };
// quantitativos e custo das colunas ia..ib-1 de um muro, com a altura real de cada coluna
function muroColunas(o,m,ia,ib,fech){
  const p=precosUso(), T=m.tab, vgW=T.g05+T.g10, q={pc:[0,0,0,0,0,0,0,0],vt:0,vg:0,face:0,pol:0,geo:0}; let hmin=1e9,hmax=0;
  for(let i=ia;i<ib;i++){ const c=m._c[i], col=m.cols[i], f=c.fT+c.fG; for(let k=0;k<8;k++) q.pc[k]+=col[2+k];
    q.vg+=vgW*(m._fG>0?c.fG/m._fG:f/m._f);            // gabiao: total do muro rateado pela face em gabiao (ou pelo muro todo, quando so ha contraforte)
    q.vt+=c.vt; q.face+=f; q.pol+=m._fT>0?T.pol*c.fT/m._fT:0; q.geo+=T.geo*f/m._f; hmin=Math.min(hmin,c.H); hmax=Math.max(hmax,c.H); }
  q.g05=vgW?q.vg*T.g05/vgW:0; q.g10=vgW?q.vg*T.g10/vgW:0; q.g4r=vgW?T.g4r*q.vg/vgW:0;
  q.rm3=o.muros.perda_rachao*(q.vt+q.vg); q.rt=q.rm3*p.dens;
  const itens=[]; let mac=0;
  const poe=(id,qt)=>{ if(qt<=1e-9) return; const it=itemPreco(o,id), v=qt*p[id]; mac+=v; itens.push({id,nome:it[1],un:it[2],q:qt,pu:p[id],v}); };
  TPK.forEach((id,k)=>poe(id,q.pc[k])); poe("g05",q.g05); poe("g10",q.g10); poe("pol",q.pol); poe("g4r",q.g4r); poe("geo",q.geo);
  const rach=q.rt*p.rach, moT=q.vt*p.moT, moG=q.vg*p.moG;
  return {m, ia, ib, sa:m.s0+ia*m.passo, sb:m.s0+ib*m.passo, comp:(ib-ia)*m.passo, fech:!!fech, hmin, hmax, q, itens, mac, rach, moT, moG, mo:moT+moG, total:mac+rach+moT+moG, p};
}
// trecho entre duas estacas, preso aos modulos de 2 m do projeto (a peca tem 2 m de largura)
function muroTrecho(o,m,sa,sb){ if(sa>sb){ const t=sa; sa=sb; sb=t; }
  const n=m._c.length, nE=Math.round((m.sE-m.s0)/m.passo); let ia=Math.round((sa-m.s0)/m.passo), ib=Math.round((sb-m.s0)/m.passo), fech=false;
  ia=Math.max(0,Math.min(nE-1,ia)); ib=Math.max(ia+1,Math.min(nE,ib));
  if(nE<n&&ib>=nE){ ib=n; fech=true; }                // o fim do eixo na planta leva junto o fechamento que so aparece na vista frontal
  return muroColunas(o,m,ia,ib,fech); }
function muroInteiro(o,m){ return muroColunas(o,m,0,m._c.length,false); }
function leituraMuro(o,rp,g){
  const b=muroPerto(o,rp.E,rp.N), nat=$("rdNat"), cfL=$("rdCfL"), cfV=$("rdCf");
  $("rdLbl").textContent = rp.gps ? "Altura do muro onde você está" : "Altura do muro na mira";
  const pre = g ? "GPS ± "+fmt(g.acc,g.acc<10?1:0)+" m, "+(S.cal?"calibrado. ":"sem calibrar. ") : "", pos="E "+fmt(rp.E,1)+" · N "+fmt(rp.N,1);
  if(!b||b.d>10){ $("rdBig").textContent="—"; cfL.textContent=""; cfV.textContent=""; nat.classList.remove("on"); nat.textContent="";
    $("rdSub").textContent="Não há muro a menos de 10 m "+(rp.gps?"de você":"da mira")+"."+(b?" O mais próximo é o "+b.m.nome+", a "+fmt(b.d,0)+" m.":"");
    $("rdSub2").textContent=pre+pos; return; }
  const m=b.m, i=muroColIdx(m,b.s), c=m._c[i], col=m.cols[i];
  $("rdBig").innerHTML=fmt(c.H)+"<small>m</small>";
  cfL.textContent="Distância ao eixo"; cfV.innerHTML=fmt(b.d,1)+"<small>m</small>";
  nat.classList.add("on"); nat.textContent="Topo "+fmt(c.top)+" m · Base "+fmt(c.base)+" m";
  const Ls=[]; for(let k=0;k<4;k++) if(col[2+k]||col[6+k]) Ls.push(5+k);
  let t=m.nome+", estaca "+estaca(b.s)+". "+(c.fT>0 ? "Terramesh com reforço de "+Ls.join(" e ")+" m." : "Trecho em gabião.");
  if(m.s1>m.sE&&b.s>=m.sE-0.5) t+=" Depois deste ponto o projeto tem mais "+fmt(m.s1-m.sE,0)+" m de fechamento no canto.";
  $("rdSub").textContent=t;
  let s2="";
  if(rp.gps){ const r=Math.max(g.acc,2); let lo=1e9,hi=0; for(let j=muroColIdx(m,b.s-r);j<=muroColIdx(m,b.s+r);j++){ lo=Math.min(lo,m._c[j].H); hi=Math.max(hi,m._c[j].H); }
    if(hi-lo>0.05) s2="Dentro da precisão do GPS a altura pode ir de "+fmt(lo)+" a "+fmt(hi)+" m. "; }
  $("rdSub2").textContent=pre+s2+pos;
}
function drawMuros(o){
  const v=S.view, M=S.mu;
  cx.lineCap="round"; cx.lineJoin="round";
  for(const m of o.muros.lista){
    cx.strokeStyle="#15130F"; cx.lineWidth=v.s>=3?6:4; cx.beginPath(); m.eixo.forEach((q,i)=>{ const x=sx(q[0]), y=sy(q[1]); i?cx.lineTo(x,y):cx.moveTo(x,y) }); cx.stroke();
    cx.strokeStyle="#FFD23F"; cx.lineWidth=v.s>=3?2:1.5; cx.beginPath(); m.eixo.forEach((q,i)=>{ const x=sx(q[0]), y=sy(q[1]); i?cx.lineTo(x,y):cx.moveTo(x,y) }); cx.stroke();
  }
  if(M.m&&M.A){ const m=M.m;
    if(M.res){ const a=M.res.sa, b=Math.min(M.res.sb,m.sE); cx.strokeStyle="#E0661A"; cx.lineWidth=10; cx.beginPath();
      for(let s=a,i=0;;s=Math.min(b,s+1),i++){ const q=muroPonto(m,s), x=sx(q.E), y=sy(q.N); i?cx.lineTo(x,y):cx.moveTo(x,y); if(s>=b) break; } cx.stroke(); }
  }
  cx.lineCap="butt"; cx.lineJoin="miter";
  for(const m of o.muros.lista){
    if(v.s>=2.5){ cx.font="700 11px Barlow, system-ui, sans-serif"; cx.textBaseline="middle";
      for(let s=Math.ceil(m.s0/20)*20; s<=m.sE+1e-6; s+=20){ const q=muroPonto(m,s), x=sx(q.E), y=sy(q.N); if(x<-40||y<-20||x>W+40||y>H+20) continue;
        cx.fillStyle="#fff"; cx.strokeStyle="#15130F"; cx.lineWidth=1.5; cx.beginPath(); cx.arc(x,y,4,0,7); cx.fill(); cx.stroke();
        if(v.s>=4){ const t=estaca(s), w=cx.measureText(t).width; cx.fillStyle="rgba(255,255,255,.92)"; cx.fillRect(x+6,y-8,w+6,16); cx.fillStyle="#15130F"; cx.fillText(t,x+9,y+.5); } } }
    const mid=muroPonto(m,(m.s0+m.sE)/2); etiqueta(sx(mid.E),sy(mid.N)-16,m.nome.toUpperCase(),"#15130F");
  }
  if(M.m&&M.A){ pino(muroPonto(M.m,M.res?M.res.sa:M.A.s),"I"); if(M.res) pino(muroPonto(M.m,Math.min(M.res.sb,M.m.sE)),"F"); }
}
function pintaBnMuro(){
  const M=S.mu, r=M.res; $("muB").disabled=!M.A; $("muCusto").disabled=!r;
  if(r){ $("muVals").textContent=r.m.nome+" · "+estaca(r.sa)+" a "+estaca(r.sb)+" · "+fmt(r.comp,0)+" m · "+brl(r.total,0);
    $("muSub").textContent="Maccaferri "+brl(r.mac,0)+" · rachão "+brl(r.rach,0)+" · mão de obra "+brl(r.mo,0)+"."+(r.fech?" Inclui o fechamento no canto.":""); }
  else if(M.A){ $("muVals").textContent="Início: "+M.m.nome+", estaca "+estaca(M.A.s); $("muSub").textContent="Eixo a "+fmt(M.A.d,1)+" m do ponto marcado. Agora marque o fim, no mesmo muro."; }
  else{ $("muVals").textContent="Marque o início do trecho"; $("muSub").textContent="O ponto marcado é onde você está (GPS) ou onde a mira está. Ele é preso ao eixo do muro mais próximo."; }
}
$("btnMuro").onclick=()=>{ if(S.modo==="muro") return modo(null); if(!S.obra||!S.obra.muros) return; modo("muro"); pintaBnMuro(); };
$("muA").onclick=()=>{ const o=S.obra, rp=pontoLeitura(), b=muroPerto(o,rp.E,rp.N);
  if(!b||b.d>10){ aviso("Não há muro a menos de 10 m deste ponto."+(b?" O mais próximo é o "+b.m.nome+", a "+fmt(b.d,0)+" m.":"")); return; }
  S.mu={A:{s:b.s,d:b.d},B:null,m:b.m,res:null}; pintaBnMuro(); atualiza(); };
$("muB").onclick=()=>{ const o=S.obra, M=S.mu, rp=pontoLeitura(); if(!M.A) return; const r=muroProj(M.m,rp.E,rp.N);
  if(r.d>10){ aviso("Este ponto está a "+fmt(r.d,0)+" m do "+M.m.nome+". Marque o fim sobre o mesmo muro do início."); return; }
  M.B={s:r.s,d:r.d}; M.res=muroTrecho(o,M.m,M.A.s,M.B.s); pintaBnMuro(); atualiza(); };
$("muClr").onclick=()=>{ S.mu={A:null,B:null,m:null,res:null}; pintaBnMuro(); atualiza(); };
$("muX").onclick=()=>modo(null);
$("muPre").onclick=()=>{ pintaPrecos(); abre("shPrecos"); };
$("muCusto").onclick=()=>{ if(S.mu.res){ pintaMuroCusto(); abre("shMuro"); } };
const qtd=(v,un)=> un==="pç" ? fmt(v,0)+" pç" : fmt(v,un==="m³"?2:1)+" "+un;
function pedidoTexto(r){
  const o=S.obra, up=v=>Math.ceil(v-1e-6), L=[];
  L.push("PEDIDO DE MATERIAL – "+o.nome); L.push(r.m.nome+", estaca "+estaca(r.sa)+" a "+estaca(r.sb)+" ("+fmt(r.comp,0)+" m de muro, "+fmt(r.q.face,0)+" m² de face)"); L.push("");
  L.push("Maccaferri:");
  for(const it of r.itens){ const q = it.un==="pç" ? fmt(it.q,0)+" pç" : it.un==="m³" ? fmt(Math.ceil(it.q*2-1e-6)/2,1)+" m³" : fmt(up(it.q),0)+" "+it.un; L.push("- "+it.nome+": "+q); }
  L.push(""); L.push("Rachão: "+fmt(up(r.q.rt),0)+" t (cerca de "+fmt(up(r.q.rm3),0)+" m³, já com 15% de perda)");
  return L.join("\n");
}
function pintaMuroCusto(){
  const r=S.mu.res=muroTrecho(S.obra,S.mu.m,S.mu.A.s,S.mu.B.s), B=$("muBody"); B.textContent="";
  B.appendChild(el("p",null,r.m.nome+", da estaca "+estaca(r.sa)+" à "+estaca(r.sb)+": "+fmt(r.comp,0)+" m de muro, "+fmt(r.q.face,0)+" m² de face, altura de "+fmt(r.hmin,1)+" a "+fmt(r.hmax,1)+" m."));
  if(r.fech) B.appendChild(el("p","note","Este trecho vai até o fim do eixo e inclui os "+fmt(r.m.s1-r.m.sE,0)+" m de fechamento que o projeto mostra só na vista frontal."));
  const grupo=(titulo,valor,linhas)=>{ const c=el("div","card"), h=el("div","gh"); h.appendChild(el("h3",null,titulo)); h.appendChild(el("b",null,brl(valor))); c.appendChild(h);
    const t=el("div","tb"); for(const l of linhas){ t.appendChild(el("span",null,l[0])); t.appendChild(el("span","n",l[1])); t.appendChild(el("span","n",l[2])); } c.appendChild(t); B.appendChild(c); };
  grupo("Materiais Maccaferri",r.mac,r.itens.map(it=>[it.nome,qtd(it.q,it.un),brl(it.v)]));
  grupo("Rachão",r.rach,[["Rachão, com 15% de perda ("+fmt(r.q.rm3,1)+" m³)",fmt(r.q.rt,1)+" t",brl(r.rach)]]);
  const mo=[]; if(r.q.vt>0) mo.push(["Montagem de Terramesh",fmt(r.q.vt,1)+" m³",brl(r.moT)]); if(r.q.vg>0) mo.push(["Montagem de gabião",fmt(r.q.vg,2)+" m³",brl(r.moG)]);
  grupo("Mão de obra",r.mo,mo);
  const tot=el("div","tot"); tot.appendChild(el("span",null,"Total do trecho")); tot.appendChild(el("b",null,brl(r.total))); B.appendChild(tot);
  B.appendChild(el("p","mute","Por metro de muro: "+brl(r.total/r.comp,0)+". Por m² de face: "+brl(r.total/r.q.face,0)+". O gabião, os arames e o geotêxtil são o total do muro no projeto, rateado pela área do trecho."));
  const c=el("div","card"); c.appendChild(el("h3",null,"Lista de pedido")); const pre=el("pre","ped",pedidoTexto(r)); c.appendChild(pre);
  const row=el("div","rowb"), bc=el("button","btn dark solid","Copiar"), wa=el("a",null,"Enviar por WhatsApp"); wa.target="_blank"; wa.rel="noopener"; wa.href="https://wa.me/?text="+encodeURIComponent(pre.textContent);
  bc.onclick=async()=>{ try{ await navigator.clipboard.writeText(pre.textContent); aviso("Lista copiada.") }catch(e){ aviso("Não deu para copiar. Segure o dedo sobre a lista e copie.") } };
  row.appendChild(bc); row.appendChild(wa); c.appendChild(row); B.appendChild(c);
  const bp=el("button","btn dark","Preços unitários"); bp.onclick=()=>{ pintaPrecos(); abre("shPrecos"); }; B.appendChild(bp);
}

/* ---------- Fundacao das casas ---------- */
// O projeto define um conjunto de 12 casas tipo 1; o app usa a media por casa desse conjunto. Somente materiais.
S.fu={sel:new Set(),q:{1:0,2:0,3:0}};
function fundCalc(o,q){ const F=o.fundacao, p=precosUso(), n=(q[1]||0)+(q[2]||0)+(q[3]||0), k=n/F.conjunto; let furos=0, metros=0;
  for(const f of F.furos){ furos+=f[0]*k; metros+=f[0]*f[1]*k; } const m3=F.baldrame_m3*k, cF=metros*p.furo, cC=m3*p.conc;
  return {n,furos,metros,cFuro:cF,m3,cConc:cC,total:cF+cC,porCasa:n?(cF+cC)/n:0,p}; }
function fundTotalTipo(o,t){ return o.fundacao.casas.filter(c=>c[2]===t).length; }
function pintaBnFund(){ const o=S.obra; if(!o||!o.fundacao) return; const r=fundCalc(o,S.fu.q);
  if(r.n){ $("fuVals").textContent=r.n+(r.n===1?" casa · ":" casas · ")+brl(r.total,0); $("fuSub").textContent="Furos "+brl(r.cFuro,0)+" · concreto do baldrame "+brl(r.cConc,0)+" · "+brl(r.porCasa,0)+" por casa."; }
  else{ $("fuVals").textContent="Toque nas casas para selecionar"; $("fuSub").textContent="Cada toque marca ou desmarca uma casa. O custo considera só materiais: furos e concreto da viga baldrame."; }
  $("fuCusto").disabled=!r.n; }
function pintaFund(){
  const o=S.obra, F=o.fundacao, B=$("fuBody"); B.textContent="";
  for(const t of F.tipos){ const max=fundTotalTipo(o,t.id); if(!max) continue;
    const c=el("div","card"), h=el("div","gh"); h.appendChild(el("h3",null,t.nome)); h.appendChild(el("span","mute",max+" no projeto")); c.appendChild(h);
    if(!t.projeto) c.appendChild(el("p","note","Sem projeto de fundação para este tipo. O custo usa os números da casa tipo 1."));
    const s=el("div","step"), bm=el("button",null,"−"), inp=el("input"), bM=el("button",null,"+"), bt=el("button","btn dark","Todas");
    inp.type="text"; inp.inputMode="numeric"; inp.value=S.fu.q[t.id]||0; inp.setAttribute("aria-label","Quantidade de "+t.nome); bm.setAttribute("aria-label","Menos uma"); bM.setAttribute("aria-label","Mais uma");
    const poe=v=>{ v=Math.max(0,Math.min(max,Math.round(v)||0)); if(S.fu.sel.size){ S.fu.sel.clear(); aviso("Quantidade digitada: a seleção feita na planta foi limpa."); } S.fu.q[t.id]=v; pintaFund(); pintaBnFund(); draw(); };
    bm.onclick=()=>poe((S.fu.q[t.id]||0)-1); bM.onclick=()=>poe((S.fu.q[t.id]||0)+1); bt.onclick=()=>poe(max); inp.onchange=()=>poe(numBR(inp.value));
    s.appendChild(bm); s.appendChild(inp); s.appendChild(bM); s.appendChild(bt); c.appendChild(s); B.appendChild(c); }
  const r=fundCalc(o,S.fu.q), c=el("div","card"), t=el("div","tb");
  const lin=(a,b,v)=>{ t.appendChild(el("span",null,a)); t.appendChild(el("span","n",b)); t.appendChild(el("span","n",v)); };
  lin("Furos de estaca Ø30 ("+fmt(r.furos,r.furos%1?1:0)+" furos)",fmt(r.metros,1)+" m",brl(r.cFuro));
  lin("Concreto da viga baldrame",fmt(r.m3,2)+" m³",brl(r.cConc));
  c.appendChild(t); B.appendChild(c);
  const tot=el("div","tot"); tot.appendChild(el("span",null,r.n+(r.n===1?" casa":" casas"))); tot.appendChild(el("b",null,brl(r.total))); B.appendChild(tot);
  B.appendChild(el("p","big2",r.n?brl(r.porCasa)+" por casa":"Escolha a quantidade de casas"));
  const f4=F.furos[0], f6=F.furos[1];
  B.appendChild(el("p","mute","Somente materiais. Média por casa do conjunto de "+F.conjunto+" casas do projeto: "+f4[0]+" furos de "+fmt(f4[1],0)+" m e "+f6[0]+" de "+fmt(f6[1],0)+" m, e "+fmt(F.baldrame_m3,2)+" m³ de concreto nas vigas baldrame. Furo a "+brl(r.p.furo)+" por metro e concreto a "+brl(r.p.conc)+" por m³. Não inclui mão de obra, aço, fôrma, concreto das estacas nem laje de piso."));
  const row=el("div","rowb"), b1=el("button","btn dark solid","Selecionar casas na planta"), b2=el("button","btn dark","Limpar"), b3=el("button","btn dark","Preços unitários");
  b1.onclick=()=>{ fecha("shFund"); modo("fund"); pintaBnFund(); if(S.view.s<4){ S.view.s=4; atualiza(); } };
  b2.onclick=()=>{ S.fu.sel.clear(); S.fu.q={1:0,2:0,3:0}; pintaFund(); pintaBnFund(); draw(); };
  b3.onclick=()=>{ pintaPrecos(); abre("shPrecos"); };
  row.appendChild(b1); row.appendChild(b2); row.appendChild(b3); B.appendChild(row);
}
$("btnFund").onclick=()=>{ if(!S.obra||!S.obra.fundacao) return; pintaFund(); abre("shFund"); };
$("fuCusto").onclick=()=>{ pintaFund(); abre("shFund"); };
$("fuClr").onclick=()=>{ S.fu.sel.clear(); S.fu.q={1:0,2:0,3:0}; pintaBnFund(); draw(); };
$("fuX").onclick=()=>modo(null);
function drawCasas(o){
  const v=S.view, sz=Math.max(7,Math.min(30,2.6*v.s)), C=o.fundacao.casas; cx.font="700 "+(sz>=18?12:10)+"px Barlow, system-ui, sans-serif"; cx.textAlign="center"; cx.textBaseline="middle";
  for(let i=0;i<C.length;i++){ const c=C[i], x=sx(c[0]), y=sy(c[1]); if(x<-30||y<-30||x>W+30||y>H+30) continue; const on=S.fu.sel.has(i);
    cx.fillStyle=on?"#E0661A":"rgba(255,255,255,.92)"; cx.strokeStyle="#15130F"; cx.lineWidth=on?2.5:1.5; cx.beginPath(); cx.rect(x-sz/2,y-sz/2,sz,sz); cx.fill(); cx.stroke();
    if(sz>=14){ cx.fillStyle=on?"#fff":"#15130F"; cx.fillText(on?"✓":(c[2]===1?"":"T"+c[2]),x,y+.5); } }
  cx.textAlign="left";
}
// toque curto na planta, no modo Fundacao, marca ou desmarca a casa mais proxima
let tap=null;
cv.addEventListener("pointerdown",e=>{ tap = ptr.size===1 ? {x:e.clientX,y:e.clientY,t:Date.now(),id:e.pointerId} : null; });
cv.addEventListener("pointerup",e=>{ const a=tap; tap=null; if(!a||a.id!==e.pointerId||S.modo!=="fund"||!S.obra||!S.obra.fundacao) return;
  if(Math.hypot(e.clientX-a.x,e.clientY-a.y)>10||Date.now()-a.t>700) return;
  const r=cv.getBoundingClientRect(), E=S.view.E+(e.clientX-r.left-W/2)/S.view.s, N=S.view.N-(e.clientY-r.top-H/2)/S.view.s, C=S.obra.fundacao.casas; let bi=-1, bd=1e9;
  for(let i=0;i<C.length;i++){ const d=Math.hypot(C[i][0]-E,C[i][1]-N); if(d<bd){ bd=d; bi=i; } }
  if(bi<0||bd>Math.max(5,22/S.view.s)) return;                  // a casa tem 3,3 x 9,9 m: vale o toque em qualquer parte dela
  const sel=S.fu.sel; if(!sel.size) S.fu.q={1:0,2:0,3:0};       // comecar a tocar zera a quantidade digitada
  sel.has(bi)?sel.delete(bi):sel.add(bi); const q={1:0,2:0,3:0}; for(const i of sel) q[C[i][2]]++; S.fu.q=q; pintaBnFund(); draw(); });

/* ---------- Tela de precos ---------- */
const GRUPOS=[["Muro: materiais Maccaferri",["t05x5","t05x6","t05x7","t05x8","t10x5","t10x6","t10x7","t10x8","g05","g10","pol","g4r","geo"]],["Muro: rachão",["rach","dens"]],["Muro: mão de obra",["moT","moG"]],["Fundação das casas",["furo","conc"]]];
function pintaPrecos(){
  const o=S.obra, B=$("prBody"), p=precosUso(), pad=precosObra(o); B.textContent="";
  for(const [titulo,ids] of GRUPOS){ const tem=ids.filter(id=>id in pad); if(!tem.length) continue; const c=el("div","card"); c.appendChild(el("h3",null,titulo));
    for(const id of tem){ const it=itemPreco(o,id), l=el("label","field pr"), mudou=p[id]!==pad[id];
      l.appendChild(el("span",null,it[1]+(id==="dens"?"":" (R$ por "+it[2]+")")+(mudou?" · orçamento: "+fmt(pad[id]):"")));
      const inp=el("input"); inp.type="text"; inp.inputMode="decimal"; inp.value=fmt(p[id]); if(mudou) inp.classList.add("mud");
      inp.onchange=()=>{ const v=numBR(inp.value); if(isNaN(v)||v<0||(id==="dens"&&v<=0)){ aviso("Valor inválido. Mantive o anterior."); } else guardaPreco(id,Math.round(v*100)/100); aposPreco(); };
      l.appendChild(inp); c.appendChild(l); }
    B.appendChild(c); }
  B.appendChild(el("p","mute","Os preços ficam guardados neste celular. Padrão: "+(o.precos.fonte||"orçamento original")+"."));
  const b=el("button","btn dark","Voltar aos preços do orçamento"); b.onclick=()=>{ try{ localStorage.removeItem("cotas.precos."+o.id) }catch(e){} aposPreco(); aviso("Preços do orçamento restaurados."); }; B.appendChild(b);
}
function aposPreco(){ pintaPrecos(); const M=S.mu; if(M.res){ M.res=muroTrecho(S.obra,M.m,M.A.s,M.B.s); if($("shMuro").classList.contains("on")) pintaMuroCusto(); } pintaBnMuro(); pintaBnFund(); if($("shFund").classList.contains("on")) pintaFund(); }
function pintaBarra(){ const o=S.obra, a=!!(o&&o.muros&&o.precos), b=!!(o&&o.fundacao&&o.precos); $("btnMuro").style.display=a?"":"none"; $("btnFund").style.display=b?"":"none"; $("barra").classList.toggle("b6",a&&b); $("barra").classList.toggle("b5",a!==b); }

