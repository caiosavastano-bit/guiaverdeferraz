# -*- coding: utf-8 -*-
# Monta o index.html novo a partir do atual: dados novos no pacote DEMO + modulos Muro e Fundacao.
import io, json, sys
SRC, OUT = sys.argv[1], sys.argv[2]
s = io.open(SRC, encoding="utf-8").read()
novo = json.load(io.open("novos_dados.json", encoding="utf-8"))
addjs = io.open("add_js.js", encoding="utf-8").read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:70])
    s = s.replace(a, b)


# ---------- dados ----------
lines = s.split("\n")
i = [k for k, l in enumerate(lines) if l.startswith("const DEMO = ")]
assert len(i) == 1
i = i[0]
line = lines[i]
obj, end = json.JSONDecoder().raw_decode(line[len("const DEMO = "):])
assert line[len("const DEMO = ") + end:].strip() == ";"
antes = json.dumps({k: obj[k] for k in obj}, ensure_ascii=False, sort_keys=True)
obj["rev"] = (obj.get("rev") or 0) + 1
obj["arquivos"] = obj.get("arquivos", []) + [
    {"papel": "Muros de arrimo", "nome": "001 a 006 - Muro de Arrimo - CALU - Rev 0.pdf", "uso": "usado: eixo dos muros (folha 2), alturas e peças por módulo de 2 m (vistas frontais) e tabela de quantidades"},
    {"papel": "Fundação das casas", "nome": "2026.02.23_ES_407_R0_CALU - Fundações, folhas 1 e 4", "uso": "usado: furos e concreto das vigas baldrame do conjunto de 12 casas"},
    {"papel": "Preços unitários", "nome": "Maccaferri QT0013511, contrato de mão de obra do muro e proposta BRMIX", "uso": "usado: preços padrão, editáveis no app"}]
for k in ("muros", "fundacao", "precos"):
    assert k not in obj
    obj[k] = novo[k]
lines[i] = "const DEMO = " + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + ";"
s = "\n".join(lines)
# as chaves antigas nao mudam (fora rev e arquivos)
chk = json.JSONDecoder().raw_decode(lines[i][len("const DEMO = "):])[0]
for k in ("formato", "id", "nome", "local", "utm", "pontos", "levantamento", "terreno", "divisa", "img"):
    assert json.dumps(chk[k], sort_keys=True) == json.dumps(json.loads(antes)[k], sort_keys=True), k

# ---------- CSS ----------
rep("</style>", """/* muro e fundacao */
.bar.b6,.bar.b5{grid-template-columns:repeat(3,1fr)}
.bar.b6 button,.bar.b5 button{min-height:44px;padding:8px 4px}
.gh{display:flex;justify-content:space-between;align-items:baseline;gap:10px}
.gh b{font-family:var(--display);font-size:22px;font-weight:700;white-space:nowrap;font-variant-numeric:tabular-nums}
.tb{display:grid;grid-template-columns:1fr auto auto;gap:6px 12px;font-size:14px;align-items:baseline}
.tb .n{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums;font-weight:600}
.tot{display:flex;justify-content:space-between;align-items:baseline;gap:10px;border-top:2px solid var(--ink);padding-top:10px}
.tot span{font-size:16px;font-weight:700}
.tot b{font-family:var(--display);font-size:38px;font-weight:700;line-height:1;font-variant-numeric:tabular-nums;white-space:nowrap}
.sheet p.big2{font-family:var(--display);font-size:24px;font-weight:700;text-align:right}
.ped{margin:0;white-space:pre-wrap;font-family:var(--body);font-size:14px;background:var(--ground);border-radius:8px;padding:10px;user-select:text;-webkit-user-select:text}
.step{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.step>button:not(.btn){width:50px;height:50px;border:1.5px solid var(--ink);border-radius:12px;font-size:28px;font-weight:700;line-height:1}
.step input{width:88px;text-align:center;font:inherit;font-family:var(--display);font-size:30px;font-weight:700;color:var(--ink);border:1.5px solid var(--ink);border-radius:10px;padding:6px;background:#fff}
.field.pr{flex-direction:row;align-items:center;justify-content:space-between;gap:10px}
.field.pr span{flex:1}
.field.pr input{width:120px;flex:none;text-align:right;font-size:17px;padding:8px 10px}
.field.pr input.mud{border-color:var(--accent);box-shadow:inset 0 0 0 1px var(--accent)}
</style>""")

# ---------- HTML ----------
rep("""  <button class="cfbtn" id="btnCF" aria-pressed="true">Corte e aterro</button>""",
    """  <div class="banner" id="bnMuro">
    <div class="vals" id="muVals">Marque o início do trecho</div>
    <p id="muSub" style="font-size:13px;color:#CFC7BA"></p>
    <div class="row"><button class="btn solid" id="muA">Marcar início</button><button class="btn solid" id="muB" disabled>Marcar fim</button><button class="btn solid" id="muCusto" disabled>Ver custo</button><button class="btn" id="muClr">Limpar</button><button class="btn" id="muPre">Preços</button><button class="btn" id="muX">Fechar</button></div>
  </div>
  <div class="banner" id="bnFund">
    <div class="vals" id="fuVals">Toque nas casas para selecionar</div>
    <p id="fuSub" style="font-size:13px;color:#CFC7BA"></p>
    <div class="row"><button class="btn solid" id="fuCusto" disabled>Ver custo</button><button class="btn" id="fuClr">Limpar</button><button class="btn" id="fuX">Fechar</button></div>
  </div>
  <button class="cfbtn" id="btnCF" aria-pressed="true">Corte e aterro</button>""")
rep("""<nav class="bar">""", """<nav class="bar" id="barra">""")
rep("""  <button id="btnDuo">2 celulares</button>
</nav>""", """  <button id="btnDuo">2 celulares</button>
  <button id="btnMuro" aria-pressed="false" style="display:none">Muro</button>
  <button id="btnFund" aria-pressed="false" style="display:none">Fundação</button>
</nav>""")
rep("""<div class="toast" id="toast" role="status"></div>""", """<!-- Custo do trecho de muro -->
<div class="sheet" id="shMuro"><div class="box">
  <div class="head"><h2>Custo do trecho de muro</h2><button class="x" data-close>Fechar</button></div>
  <div id="muBody" style="display:flex;flex-direction:column;gap:12px"></div>
</div></div>

<!-- Fundacao das casas -->
<div class="sheet" id="shFund"><div class="box">
  <div class="head"><h2>Fundação das casas</h2><button class="x" data-close>Fechar</button></div>
  <div id="fuBody" style="display:flex;flex-direction:column;gap:12px"></div>
</div></div>

<!-- Precos unitarios -->
<div class="sheet" id="shPrecos" style="z-index:30"><div class="box">
  <div class="head"><h2>Preços unitários</h2><button class="x" data-close>Fechar</button></div>
  <div id="prBody" style="display:flex;flex-direction:column;gap:12px"></div>
</div></div>

<div class="toast" id="toast" role="status"></div>""")

# ---------- JS ----------
rep("""  S.obra=o; S.img=null; S.med={A:null,B:null}; S.cal=null;""",
    """  S.obra=o; S.img=null; S.med={A:null,B:null}; S.cal=null;
  S.mu={A:null,B:null,m:null,res:null}; S.fu={sel:new Set(),q:{1:0,2:0,3:0}}; preparaMuros(o); pintaBarra();
  if(S.modo==="muro"||S.modo==="fund"){ S.modo=null; $("bnMuro").classList.remove("on"); $("bnFund").classList.remove("on"); $("btnMuro").setAttribute("aria-pressed","false"); $("btnFund").setAttribute("aria-pressed","false"); $("btnCF").style.visibility="visible"; }""")
rep("""+" · UTM zona "+o.utm.zona""", """+(o.muros?" · "+o.muros.lista.length+" muros de arrimo":"")+(o.fundacao?" · fundação de "+o.fundacao.casas.length+" casas":"")+" · UTM zona "+o.utm.zona""")
rep("""  // medicao
  const M=S.med, rp=pontoLeitura();""", """  // muros de arrimo e casas (so com o modulo ligado)
  if(S.modo==="muro"&&o.muros) drawMuros(o);
  if(S.modo==="fund"&&o.fundacao) drawCasas(o);
  // medicao
  const M=S.med, rp=pontoLeitura();""")
rep("""  pl.textContent=linha; pl.classList.toggle("on",!!linha);
  draw();
}""", """  pl.textContent=linha; pl.classList.toggle("on",!!linha);
  if(S.modo==="muro"&&o.muros) leituraMuro(o,rp,g);
  draw();
}""")
rep("""function modo(m){ S.modo=m; $("bnCal").classList.toggle("on",m==="cal"); $("bnMed").classList.toggle("on",m==="med"); $("btnCF").style.visibility=m?"hidden":"visible"; pintaCF();
  $("btnCal").setAttribute("aria-pressed",m==="cal"); $("btnMed").setAttribute("aria-pressed",m==="med"); atualiza(); }""",
    """function modo(m){ S.modo=m; $("bnCal").classList.toggle("on",m==="cal"); $("bnMed").classList.toggle("on",m==="med"); $("bnMuro").classList.toggle("on",m==="muro"); $("bnFund").classList.toggle("on",m==="fund"); $("btnCF").style.visibility=m?"hidden":"visible"; pintaCF();
  $("btnCal").setAttribute("aria-pressed",m==="cal"); $("btnMed").setAttribute("aria-pressed",m==="med"); $("btnMuro").setAttribute("aria-pressed",m==="muro"); $("btnFund").setAttribute("aria-pressed",m==="fund"); atualiza(); }""")
rep("""/* ---------- Folhas e avisos ---------- */""", addjs + """/* ---------- Folhas e avisos ---------- */""")
rep("""window.__cotas={S,llToUtm,cotaProjeto,natural};""", """window.__cotas={S,llToUtm,cotaProjeto,natural,muroPerto,muroTrecho,muroInteiro,fundCalc,precosUso,pedidoTexto};""")
io.open(OUT, "w", encoding="utf-8", newline="\n").write(s)
print("ok", len(s))
