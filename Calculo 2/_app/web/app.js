/* ---------- Renderizador Markdown próprio (rápido e sem dependências externas) ---------- */
const PIPE = "@@PIPE@@";
function esc(t){ return String(t ?? "").replace(/[&<>]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[c])); }
function inline(t){
  t = esc(t);
  t = t.replace(/`([^`]+)`/g, (m,a) => "<code>" + a + "</code>");
  t = t.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  t = t.replace(/(^|[\s(])\*([^*\n]+)\*/g, "$1<em>$2</em>");
  t = t.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  t = t.replace(/\\\|/g, "|");
  t = t.split(PIPE).join("|");
  return t;
}
function cells(line){
  return line.replace(/\\\|/g, PIPE).replace(/^\s*\|/, "").replace(/\|\s*$/, "")
             .split("|").map(c => c.trim());
}
function md2html(src){
  const L = String(src || "").replace(/\r/g, "").split("\n");
  let out = "", i = 0, list = null;
  const closeList = () => { if (list){ out += "</" + list + ">"; list = null; } };
  while (i < L.length){
    const ln = L[i];
    if (/^```/.test(ln)){
      closeList(); i++; const buf = [];
      while (i < L.length && !/^```/.test(L[i])) buf.push(L[i++]);
      i++; out += "<pre><code>" + esc(buf.join("\n")) + "</code></pre>"; continue;
    }
    if (/^\s*\|.*\|\s*$/.test(ln) && i + 1 < L.length && /^\s*\|[\s:|-]+\|\s*$/.test(L[i+1])){
      closeList();
      const head = cells(ln); i += 2;
      const rows = [];
      while (i < L.length && /^\s*\|.*\|\s*$/.test(L[i])) rows.push(cells(L[i++]));
      out += "<table><thead><tr>" + head.map(c => "<th>" + inline(c) + "</th>").join("") +
             "</tr></thead><tbody>" +
             rows.map(r => "<tr>" + r.map(c => "<td>" + inline(c) + "</td>").join("") + "</tr>").join("") +
             "</tbody></table>";
      continue;
    }
    let m;
    if ((m = ln.match(/^(#{1,4})\s+(.*)$/))){
      closeList(); out += "<h" + m[1].length + ">" + inline(m[2]) + "</h" + m[1].length + ">"; i++; continue;
    }
    if (/^\s*(---|\*\*\*)\s*$/.test(ln)){ closeList(); out += "<hr>"; i++; continue; }
    if (/^>\s?/.test(ln)){
      closeList(); const buf = [];
      while (i < L.length && /^>\s?/.test(L[i])) buf.push(L[i++].replace(/^>\s?/, ""));
      out += "<blockquote>" + md2html(buf.join("\n")) + "</blockquote>"; continue;
    }
    if ((m = ln.match(/^\s*[-*]\s+(.*)$/))){
      if (list !== "ul"){ closeList(); out += "<ul>"; list = "ul"; }
      out += "<li>" + inline(m[1]) + "</li>"; i++; continue;
    }
    if ((m = ln.match(/^\s*\d+\.\s+(.*)$/))){
      if (list !== "ol"){ closeList(); out += "<ol>"; list = "ol"; }
      out += "<li>" + inline(m[1]) + "</li>"; i++; continue;
    }
    if (!ln.trim()){ closeList(); i++; continue; }
    const para = [];
    while (i < L.length && L[i].trim() &&
           !/^(#{1,4}\s|>|\s*[-*]\s|\s*\d+\.\s|```)/.test(L[i]) &&
           !/^\s*\|.*\|\s*$/.test(L[i]) && !/^\s*---\s*$/.test(L[i])) para.push(L[i++]);
    if (para.length){ closeList(); out += "<p>" + inline(para.join(" ")) + "</p>"; }
    else { i++; }
  }
  closeList();
  return out;
}

/* ---------- Estado Global e Comunicação com o Servidor ---------- */
let DADOS = null;
let CURSO = null;
let STATUS = {};
let salvarTimer = null;
let ULTIMO_PROMPT_RAG = "";

const LBL = { ok: "✓", err: "✗", dub: "?" };
const TIP = { ok: "acertei", err: "errei", dub: "dúvida" };
const ORDINAL = { 1: "1ª", 2: "2ª", 3: "3ª" };

const paramsUrl = new URLSearchParams(location.search);
let DISC = paramsUrl.get("d") || "Calculo 2";
let UN = ["1", "2", "3"].includes(paramsUrl.get("u")) ? Number(paramsUrl.get("u")) : null;

function setBadge(txt, cls) {
  const b = document.getElementById("syncbadge");
  if (b) { b.textContent = txt; b.className = "syncbadge " + cls; }
}

function urlArquivo(caminhoRel) {
  if (!caminhoRel) return "#";
  const [base, hash] = String(caminhoRel).split("#");
  const partes = base.split("/").map(encodeURIComponent).join("/");
  return "/arquivos/" + encodeURIComponent(DISC) + "/" + partes + (hash ? "#" + hash : "");
}

function escolherUnidadePorData(curso) {
  const hoje = new Date(); hoje.setHours(0, 0, 0, 0);
  const uns = (curso && curso.unidades) || {};
  for (const u of [1, 2, 3]) {
    const dp = uns[String(u)] && uns[String(u)].dataProva;
    if (dp) {
      const [a, m, d] = dp.split("-").map(Number);
      if (hoje <= new Date(a, m - 1, d)) return u;
    }
  }
  return 3;
}

async function carregar() {
  setBadge("lendo a pasta…", "wait");
  try {
    const r = await fetch("/api/dados?disciplina=" + encodeURIComponent(DISC), { cache: "no-store" });
    if (!r.ok) throw new Error("HTTP " + r.status);
    DADOS = await r.json();
    DISC = DADOS.disciplinaAtual || DISC;
    CURSO = DADOS.curso || {};
    STATUS = DADOS.status || {};
    if (!UN) UN = escolherUnidadePorData(CURSO);

    renderSeletorDisciplina();
    aplicarUnidadeUI();
    renderCurso();
    renderExercicios();
    renderAbas();
    renderPdfsQuickBar();
    tally();
    atualizarBotaoUndo();
    popularDrawerAgente();
    setBadge("salvo na pasta", "ok");
  } catch (e) {
    console.error(e);
    setBadge("servidor fora do ar", "local");
  }
}

function atualizarBotaoUndo() {
  const btn = document.getElementById("btnUndo");
  if (!btn) return;
  const hist = (DADOS && DADOS.historicoUndo) || [];
  if (hist.length > 0) {
    btn.hidden = false;
    btn.title = "Desfazer: " + hist[0].descricao + " (" + hist[0].arquivo + ")";
    btn.textContent = "↩ Desfazer (" + hist.length + ")";
  } else {
    btn.hidden = true;
  }
}

async function salvarCurso(descricao, destravarSecoes = []) {
  setBadge("gravando curso…", "wait");
  try {
    const r = await fetch("/api/curso", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        disciplina: DISC,
        curso: CURSO,
        descricao: descricao || "Edição na interface",
        destravarSecoes,
      }),
    });
    if (!r.ok) throw new Error("HTTP " + r.status);
    await carregar();
  } catch (e) {
    alert("Erro ao salvar curso.json: " + e.message);
    setBadge("erro ao salvar", "local");
  }
}

function salvarStatus() {
  clearTimeout(salvarTimer);
  setBadge("salvando…", "wait");
  salvarTimer = setTimeout(async () => {
    try {
      const r = await fetch("/api/status", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ disciplina: DISC, marcacoes: STATUS }),
      });
      if (!r.ok) throw new Error("HTTP " + r.status);
      salvarTimer = null;
      setBadge("salvo na pasta", "ok");
    } catch (e) {
      setBadge("não salvou — servidor fora?", "local");
    }
  }, 300);
}

/* ---------- Seletor de Disciplinas e Unidades ---------- */
function renderSeletorDisciplina() {
  const sel = document.getElementById("selDisciplina");
  if (!sel || !DADOS) return;
  sel.innerHTML = "";
  (DADOS.disciplinas || []).forEach(d => {
    const opt = document.createElement("option");
    opt.value = d.pasta;
    opt.textContent = d.nome;
    if (d.pasta === DISC) opt.selected = true;
    sel.appendChild(opt);
  });
}

document.getElementById("selDisciplina")?.addEventListener("change", e => {
  DISC = e.target.value;
  const url = new URL(location.href);
  url.searchParams.set("d", DISC);
  history.replaceState(null, "", url);
  carregar();
});

function aplicarUnidadeUI(gravarUrl = false) {
  document.querySelectorAll(".unisel button").forEach(b =>
    b.setAttribute("aria-pressed", b.dataset.u === String(UN) ? "true" : "false")
  );
  const nomeCurso = (CURSO && CURSO.nome) || DISC;
  document.title = `${nomeCurso} — ${ORDINAL[UN] || UN + "ª"} unidade`;
  if (gravarUrl) {
    const url = new URL(location.href);
    url.searchParams.set("u", UN);
    url.searchParams.set("d", DISC);
    history.replaceState(null, "", url);
  }
}

document.querySelectorAll(".unisel button").forEach(b =>
  b.addEventListener("click", () => {
    UN = Number(b.dataset.u);
    aplicarUnidadeUI(true);
    if (DADOS) {
      renderCurso();
      renderExercicios();
      renderAbas();
      tally();
    }
  })
);

/* ---------- Renderização Dinâmica do Curso (Header, Onde Estamos, Cronograma, Formulário) ---------- */
function dadosUnidadeAtual() {
  const uns = (CURSO && CURSO.unidades) || {};
  return uns[String(UN)] || {
    numero: UN,
    ordinal: ORDINAL[UN] || `${UN}ª`,
    eyebrow: `${CURSO?.subtituloGeral || ""} · ${ORDINAL[UN]} unidade`,
    titulo: CURSO?.nome || DISC,
    tituloItalico: `${ORDINAL[UN]} unidade`,
    subtitulo: "",
    dataProva: "",
    tags: [],
    ondeEstamos: [],
    fases: [],
    formulario: [],
  };
}

function textoContagemProva(dataIso) {
  if (!dataIso) return "sem data definida";
  const [a, m, d] = dataIso.split("-").map(Number);
  if (!a || !m || !d) return dataIso;
  const hoje = new Date(); hoje.setHours(0, 0, 0, 0);
  const dias = Math.round((new Date(a, m - 1, d) - hoje) / 86400000);
  const fmt = String(d).padStart(2, "0") + "/" + String(m).padStart(2, "0");
  return dias > 1 ? `faltam ${dias} dias (${fmt})`
    : dias === 1 ? `é amanhã (${fmt})`
    : dias === 0 ? `é hoje (${fmt})`
    : `feita em ${fmt}`;
}

function renderCurso() {
  const u = dadosUnidadeAtual();

  // 1. Header
  const headerHost = document.getElementById("headerHost");
  if (headerHost) {
    const tagsHtml = (u.tags || []).map(t => `<span class="tag">${esc(t)}</span>`).join("");
    headerHost.innerHTML = `
      <div class="hd">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap">
          <span class="eyebrow">${esc(u.eyebrow || CURSO.subtituloGeral || "")}</span>
          <button type="button" class="actbtn small" id="btnEditHeader">✎ Editar Cabeçalho / Nota da Prova</button>
        </div>
        <h1>${esc(u.titulo || CURSO.nome || DISC)}<br><em>${esc(u.tituloItalico || u.ordinal + " unidade")}</em></h1>
        <p class="sub">${esc(u.subtitulo || "")}</p>
        <div class="meta">${tagsHtml}</div>
      </div>
    `;
    document.getElementById("btnEditHeader")?.addEventListener("click", abrirModalEditarHeader);
  }

  // 2. Onde estamos (Escadinha interativa)
  const stSub = document.getElementById("statusSubtitulo");
  if (stSub) stSub.textContent = u.ondeEstamosSubtitulo || "";
  const ladderHost = document.getElementById("ladderHost");
  if (ladderHost) {
    ladderHost.innerHTML = "";
    const lista = u.ondeEstamos || [];
    if (!lista.length) {
      ladderHost.innerHTML = '<div class="vazio">Nenhum tópico cadastrado nesta unidade. Clique em <b>+ Adicionar Tópico</b> acima.</div>';
    } else {
      lista.forEach((item, idx) => {
        const row = document.createElement("div");
        row.className = "rung " + (item.status || "later");

        const btnLv = document.createElement("button");
        btnLv.type = "button";
        btnLv.className = "lv lv-btn";
        btnLv.textContent = item.lv || (item.status === "seen" ? "Visto" : "Pendente");
        btnLv.title = "Clique para alternar: Depois → Próxima → Visto (e destravar exercícios vinculados)";
        btnLv.addEventListener("click", () => {
          const ordem = ["later", "next", "seen"];
          const prox = ordem[(ordem.indexOf(item.status) + 1) % ordem.length] || "seen";
          item.status = prox;
          if (prox === "seen") {
            item.lvAnter = item.lv !== "Visto" ? item.lv : item.lvAnter;
            item.lv = "Visto";
          } else if (prox === "next") {
            item.lv = item.lvAnter || "Próxima";
          } else {
            item.lv = item.lvAnter || "Depois";
          }
          const destravar = prox === "seen" ? (item.secoes || []) : [];
          salvarCurso(`Marcar tópico '${item.titulo}' como ${prox}`, destravar);
        });

        const mid = document.createElement("div");
        mid.innerHTML = `<strong>${item.titulo}</strong><small>${item.detalhe || ""}</small>`;

        const right = document.createElement("div");
        right.className = "rung-actions";
        const secsBadge = (item.secoes && item.secoes.length)
          ? `<span class="tag" title="Seções de exercícios vinculadas">${esc(item.secoes.join(", "))}</span>`
          : "";
        right.innerHTML = `${secsBadge}<span class="where">${esc(item.where || "")}</span>`;

        const btnEdit = document.createElement("button");
        btnEdit.type = "button";
        btnEdit.className = "iconbtn";
        btnEdit.textContent = "✎";
        btnEdit.title = "Editar tópico";
        btnEdit.addEventListener("click", () => abrirModalTopico(idx));

        const btnDel = document.createElement("button");
        btnDel.type = "button";
        btnDel.className = "iconbtn";
        btnDel.textContent = "✕";
        btnDel.title = "Remover tópico";
        btnDel.addEventListener("click", () => {
          if (!confirm(`Remover o tópico "${item.titulo}"?`)) return;
          u.ondeEstamos.splice(idx, 1);
          salvarCurso(`Remover tópico '${item.titulo}'`);
        });

        right.append(btnEdit, btnDel);
        row.append(btnLv, mid, right);
        ladderHost.appendChild(row);
      });
    }
  }

  // 3. Cronograma
  document.getElementById("cronoTitulo").textContent = u.cronogramaTitulo || "Cronograma";
  document.getElementById("cronoSubtitulo").textContent = u.cronogramaSubtitulo || "";
  document.getElementById("cronoContagem").textContent = textoContagemProva(u.dataProva);

  const cronoHost = document.getElementById("cronoHost");
  if (cronoHost) {
    cronoHost.innerHTML = "";
    (u.fases || []).forEach((fase, fIdx) => {
      const box = document.createElement("div");
      box.className = "fase " + (fase.estilo || "f1");
      const cols = fase.colunas || ["Sessão", "Data", "Foco", "Exercícios"];
      const ths = cols.map(c => `<th>${esc(c)}</th>`).join("") + `<th>Ações</th>`;

      let trs = "";
      (fase.linhas || []).forEach((ln, lIdx) => {
        const xCols = (ln.x || []).map(xVal => `<td class="x">${xVal}</td>`).join("");
        trs += `
          <tr class="${ln.feito ? "sessao-feita" : ""}">
            <td class="s">
              <label style="display:inline-flex;align-items:center;cursor:pointer">
                <input type="checkbox" class="crono-chk" data-f="${fIdx}" data-l="${lIdx}" ${ln.feito ? "checked" : ""}>
                ${esc(ln.s || "")}
              </label>
            </td>
            ${cols.length > 2 ? `<td class="d">${esc(ln.d || "")}</td>` : ""}
            <td class="t">${ln.t || ""}</td>
            ${xCols}
            <td style="white-space:nowrap;width:64px">
              <button type="button" class="iconbtn btn-edit-sessao" data-f="${fIdx}" data-l="${lIdx}" title="Editar linha">✎</button>
              <button type="button" class="iconbtn btn-del-sessao" data-f="${fIdx}" data-l="${lIdx}" title="Excluir linha">✕</button>
            </td>
          </tr>
        `;
      });

      box.innerHTML = `
        <header>
          <div><span class="eyebrow">${esc(fase.eyebrow || "")}</span><h3>${esc(fase.titulo || "")}</h3></div>
          <span class="tag">${esc(fase.tag || "")}</span>
        </header>
        <div class="tablewrap">
          <table>
            <thead><tr>${ths}</tr></thead>
            <tbody>${trs}</tbody>
          </table>
        </div>
        ${fase.nota ? `<p class="note" style="margin:12px 18px">${fase.nota}</p>` : ""}
      `;
      cronoHost.appendChild(box);
    });

    cronoHost.querySelectorAll(".crono-chk").forEach(chk => {
      chk.addEventListener("change", e => {
        const f = Number(e.target.dataset.f), l = Number(e.target.dataset.l);
        u.fases[f].linhas[l].feito = e.target.checked;
        salvarCurso(`Marcar sessão ${u.fases[f].linhas[l].s} no cronograma`);
      });
    });
    cronoHost.querySelectorAll(".btn-edit-sessao").forEach(b => {
      b.addEventListener("click", () => abrirModalSessaoCrono(Number(b.dataset.f), Number(b.dataset.l)));
    });
    cronoHost.querySelectorAll(".btn-del-sessao").forEach(b => {
      b.addEventListener("click", () => {
        const f = Number(b.dataset.f), l = Number(b.dataset.l);
        const sNome = u.fases[f].linhas[l].s;
        if (!confirm(`Remover a sessão ${sNome} do cronograma?`)) return;
        u.fases[f].linhas.splice(l, 1);
        salvarCurso(`Remover sessão ${sNome}`);
      });
    });
  }

  // 4. Resumos subtitle & Formulário
  document.getElementById("resumosSubtitulo").textContent = u.resumosSubtitulo || "";
  document.getElementById("formTitulo").textContent = u.formularioTitulo || `Formulário essencial — ${u.ordinal} unidade`;
  document.getElementById("formSubtitulo").textContent = u.formularioSubtitulo || "";

  const formHost = document.getElementById("formHost");
  if (formHost) {
    formHost.innerHTML = "";
    const cards = u.formulario || [];
    if (!cards.length) {
      formHost.innerHTML = `<div class="vazio">Nenhuma fórmula cadastrada nesta unidade ainda. Clique em <b>+ Adicionar Fórmula</b> ou gere um resumo com o Agente.</div>`;
    } else {
      cards.forEach((c, idx) => {
        const div = document.createElement("div");
        div.className = "fcard";
        const notasHtml = (c.notas || []).map(n => `<p>${n}</p>`).join("");
        div.innerHTML = `
          <div class="fcard-head">
            <h3>${esc(c.titulo)}</h3>
            <div>
              <button type="button" class="iconbtn" data-edit="${idx}" title="Editar fórmula">✎</button>
              <button type="button" class="iconbtn" data-del="${idx}" title="Excluir fórmula">✕</button>
            </div>
          </div>
          <div class="fml">${esc(c.fml)}</div>
          ${notasHtml}
        `;
        div.querySelector("[data-edit]")?.addEventListener("click", () => abrirModalFormula(idx));
        div.querySelector("[data-del]")?.addEventListener("click", () => {
          if (!confirm(`Remover o cartão "${c.titulo}" do formulário?`)) return;
          u.formulario.splice(idx, 1);
          salvarCurso(`Remover fórmula '${c.titulo}'`);
        });
        formHost.appendChild(div);
      });
    }
  }

  // 5. Footer
  document.getElementById("footerDiscNome").textContent = `${CURSO.nome || DISC} (${CURSO.subtituloGeral || ""})`;
  document.getElementById("footerAtualizado").textContent = `atualizado em ${CURSO.atualizadoEm || "hoje"}`;
}

function renderPdfsQuickBar() {
  const bar = document.getElementById("pdfsQuickBar");
  if (!bar || !DADOS) return;
  bar.innerHTML = "";
  (DADOS.arquivosPdf || []).slice(0, 8).forEach(pdf => {
    const a = document.createElement("a");
    a.className = "actbtn small";
    a.href = urlArquivo(pdf.caminho);
    a.target = "_blank";
    a.rel = "noopener";
    a.textContent = "📄 " + pdf.nome;
    bar.appendChild(a);
  });
}

/* ---------- Exercícios & Resoluções + Botões N1..N4 + Destravar Seção ---------- */
const UN_POR_SEC = {
  "14.1":1,"14.2":1,"14.3":1,"14.4":1,"14.5":1,
  "14.6":2,"14.7":2,"14.8":2,"15.2":2,"15.3":2,"L3":2,"L4":2,
  "15.4":3,"15.5":3,"15.7":3,"15.8":3,"15.9":3,"15.10":3,"L5":3,"L6":3
};
const unDaSecao = s => Number(s.un || UN_POR_SEC[s.sec] || 1);
const secoesDaUnidade = () => (DADOS?.exercicios || []).filter(s => unDaSecao(s) === UN);

function renderExercicios() {
  const host = document.getElementById("exhost");
  if (!host) return;
  host.innerHTML = "";

  const secoes = secoesDaUnidade();
  if (!secoes.length) {
    host.innerHTML = `<div class="vazio"><strong>Nenhuma lista ou seção cadastrada na ${ORDINAL[UN]} unidade.</strong> Clique em <b>+ Nova Lista / Seção</b> acima para criar em segundos.</div>`;
    return;
  }

  secoes.forEach(s => {
    const box = document.createElement("div");
    box.className = "secbox" + (s.locked ? " locked" : "");
    box.dataset.open = "false";
    box.dataset.sec = s.sec;

    const bodyId = "body-" + String(s.sec).replace(/[^a-zA-Z0-9_-]/g, "-");
    const headWrap = document.createElement("div");
    headWrap.className = "sec-head-wrap";

    const tog = document.createElement("button");
    tog.className = "sectoggle";
    tog.type = "button";
    tog.setAttribute("aria-expanded", "false");
    tog.setAttribute("aria-controls", bodyId);
    tog.innerHTML =
      `<span class="caret">▸</span>` +
      `<span class="sectitle">${esc(s.sec)} <span>${esc(s.nome)}</span></span>` +
      `<span class="seccount"></span>` +
      `<span class="secpct"></span>` +
      `<span class="secpg">${esc(s.pg || "")}</span>`;

    const toolsDiv = document.createElement("div");
    toolsDiv.className = "sec-head-tools";

    if (s.pdf) {
      const aPdf = document.createElement("a");
      aPdf.className = "actbtn small";
      aPdf.href = urlArquivo(s.pdf);
      aPdf.target = "_blank";
      aPdf.rel = "noopener";
      aPdf.textContent = "📄 PDF";
      aPdf.title = "Abrir PDF desta lista/seção em nova aba";
      toolsDiv.appendChild(aPdf);
    }

    const btnLock = document.createElement("button");
    btnLock.type = "button";
    btnLock.className = "actbtn small";
    btnLock.textContent = s.locked ? "🔒 Travada" : "🔓 Ativa";
    btnLock.title = s.locked
      ? "Clique para destravar esta seção e incluí-la no placar da unidade"
      : "Clique para travar esta seção";
    btnLock.addEventListener("click", async () => {
      await fetch("/api/exercicios", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ disciplina: DISC, acao: "toggle_lock", sec: s.sec }),
      });
      await carregar();
    });
    toolsDiv.appendChild(btnLock);

    headWrap.append(tog, toolsDiv);
    box.appendChild(headWrap);

    const body = document.createElement("div");
    body.className = "secbody";
    body.id = bodyId;
    body.hidden = true;

    [["Linha 1 — prioridade / essenciais", "l1"], ["Linha 2 — reforço", "l2"]].forEach(([rotulo, k]) => {
      const itens = s[k] || [];
      if (!itens.length) return;
      const lh = document.createElement("div");
      lh.className = "linehead";
      lh.textContent = rotulo;
      body.appendChild(lh);

      itens.forEach(item => {
        const n = item[0], pede = item[1] || "", fn = item[2], imgKey = item[3];
        const id = s.sec + "-" + n;
        const row = document.createElement("div");
        row.className = "exrow";
        if (STATUS[id]) row.dataset.state = STATUS[id];

        const num = document.createElement("div");
        num.className = "exnum";
        num.textContent = n;

        const q = document.createElement("div");
        q.className = "exq";
        q.innerHTML = pede + (fn ? `<br><span class="fn">${esc(fn)}</span>` : "");

        const right = document.createElement("div");
        right.className = "exright";

        // Barra N1 | N2 | N3 | N4 que aciona a Skill tutor-progressivo no Agente
        const nbar = document.createElement("div");
        nbar.className = "nbar";
        nbar.title = "Acionar Tutor Progressivo (RAG + Conferência Matemática)";
        ["N1", "N2", "N3", "N4"].forEach(nv => {
          const nb = document.createElement("button");
          nb.type = "button";
          nb.textContent = nv;
          nb.title = `Pedir ${nv} do exercício ${s.sec} #${n} ao Agente`;
          nb.addEventListener("click", () => abrirAgenteParaExercicio(s.sec, n, nv));
          nbar.appendChild(nb);
        });
        right.appendChild(nbar);

        // Botões ✓ / ✗ / ?
        const seg = document.createElement("div");
        seg.className = "seg";
        seg.setAttribute("role", "group");
        ["ok", "err", "dub"].forEach(v => {
          const b = document.createElement("button");
          b.type = "button";
          b.dataset.v = v;
          b.textContent = LBL[v];
          b.title = TIP[v];
          b.setAttribute("aria-pressed", STATUS[id] === v ? "true" : "false");
          b.addEventListener("click", () => {
            if (STATUS[id] === v) delete STATUS[id]; else STATUS[id] = v;
            seg.querySelectorAll("button").forEach(x =>
              x.setAttribute("aria-pressed", STATUS[id] === x.dataset.v ? "true" : "false")
            );
            if (STATUS[id]) row.dataset.state = STATUS[id]; else delete row.dataset.state;
            tally();
            salvarStatus();
          });
          seg.appendChild(b);
        });
        right.appendChild(seg);

        const sol = DADOS.resolucoes[id] || DADOS.resolucoes[id.replace(".", "-")];
        const sb = document.createElement("button");
        sb.className = "solbtn";
        sb.type = "button";
        if (sol) {
          sb.textContent = "ver resolução";
          const panel = document.createElement("div");
          panel.className = "solbody md";
          panel.hidden = true;
          const montar = () => {
            if (panel.dataset.pronto) return;
            const temImg = imgKey && DADOS.figuras.indexOf(imgKey) >= 0;
            panel.innerHTML =
              `<div style="display:flex;justify-content:flex-end;margin-bottom:6px">` +
              `<button type="button" class="actbtn small btn-edit-sol">✎ Editar Resolução (.md)</button></div>` +
              md2html(sol) +
              (temImg
                ? `<img src="/img/${encodeURIComponent(DISC)}/${encodeURIComponent(imgKey)}.png" loading="lazy" alt="Figura ${esc(n)}">`
                : "");
            panel.querySelector(".btn-edit-sol")?.addEventListener("click", () =>
              abrirModalMarkdown("resolucao", id, sol)
            );
            panel.dataset.pronto = "1";
          };
          sb.addEventListener("click", () => {
            if (panel.hidden) montar();
            panel.hidden = !panel.hidden;
            sb.textContent = panel.hidden ? "ver resolução" : "ocultar";
          });
          right.appendChild(sb);
          row.append(num, q, right, panel);
        } else {
          sb.textContent = "+ resolução";
          sb.title = "Escrever/colar resolução ou clique em N4 ao lado para gerar com o Agente";
          sb.addEventListener("click", () =>
            abrirModalMarkdown("resolucao", id, `**Enunciado.** ${pede} ${fn || ""}\n\n**Resposta.** \n\n**Armadilha.** `)
          );
          right.appendChild(sb);
          row.append(num, q, right);
        }
        body.appendChild(row);
      });
    });

    box.appendChild(body);
    tog.addEventListener("click", () => {
      const aberto = box.dataset.open === "true";
      box.dataset.open = aberto ? "false" : "true";
      body.hidden = aberto;
      tog.setAttribute("aria-expanded", aberto ? "false" : "true");
    });
    host.appendChild(box);
  });
}

/* ---------- Placar (Tally) ---------- */
function contar(ids) {
  let ok = 0, err = 0, dub = 0;
  ids.forEach(id => {
    const v = STATUS[id];
    if (v === "ok") ok++; else if (v === "err") err++; else if (v === "dub") dub++;
  });
  return { ok, err, dub, feitos: ok + err + dub, total: ids.length, ids };
}
function idsDe(secoes, linhas) {
  return secoes.flatMap(s => linhas.flatMap(l => (s[l] || []).map(e => s.sec + "-" + e[0])));
}

function tally() {
  if (!DADOS) return;
  const abertas = secoesDaUnidade().filter(s => !s.locked);
  const g = contar(idsDe(abertas, ["l1", "l2"]));
  const a = contar(idsDe(abertas, ["l1"]));
  const b = contar(idsDe(abertas, ["l2"]));
  const den = g.total || 1;

  document.getElementById("pFeitos").textContent = g.feitos + "/" + g.total;
  document.getElementById("pSplit").textContent =
    `feitos na ${ORDINAL[UN]} unidade — linha 1: ${a.feitos}/${a.total} · linha 2: ${b.feitos}/${b.total}`;
  document.getElementById("pErr").textContent = String(g.err + g.dub);
  document.getElementById("pAcerto").textContent =
    (g.ok + g.err) ? Math.round(g.ok / (g.ok + g.err) * 100) + "%" : "—";
  document.getElementById("bOk").style.width = (g.ok / den * 100) + "%";
  document.getElementById("bErr").style.width = (g.err / den * 100) + "%";
  document.getElementById("bDub").style.width = (g.dub / den * 100) + "%";
  const daUnidade = new Set(g.ids);
  document.getElementById("pSol").textContent =
    String(Object.keys(DADOS.resolucoes).filter(k => daUnidade.has(k)).length);

  secoesDaUnidade().forEach(s => {
    const cab = document.querySelector(`[data-sec="${CSS.escape(s.sec)}"]`);
    if (!cab) return;
    const c = contar(idsDe([s], ["l1", "l2"]));
    const alvo = cab.querySelector(".seccount");
    alvo.textContent = c.feitos ? `${c.feitos}/${c.total}` : `${c.total} questões`;
    alvo.dataset.cheio = (c.feitos && c.feitos === c.total) ? "true" : "false";

    const pct = cab.querySelector(".secpct");
    const corrigidos = c.ok + c.err;
    if (!corrigidos) {
      pct.textContent = "";
      pct.removeAttribute("data-faixa");
      return;
    }
    const taxa = Math.round(c.ok / corrigidos * 100);
    pct.textContent = taxa + "%";
    pct.dataset.faixa = taxa >= 70 ? "alta" : taxa >= 40 ? "media" : "baixa";
  });
}

/* ---------- Abas de Resumos e Documentos ---------- */
function unDoResumo(r) {
  if (r.un) return Number(r.un);
  const n = parseInt(r.key, 10);
  return Number.isNaN(n) ? UN : n <= 5 ? 1 : n <= 11 ? 2 : 3;
}
function resumoNaUnidade(r) {
  const extra = (CURSO?.resumosExtraUnidade || {})[r.key] || [];
  return unDoResumo(r) === UN || extra.includes(UN);
}
function docNaUnidade(r) {
  const us = r.unidades;
  return !us || !us.length || us.includes(UN);
}

let RESUMO_ATUAL = null;

function renderAbas() {
  const grupos = [
    {
      grupo: "resumo",
      tabs: "tabsResumos",
      pane: "paneResumos",
      src: "srcResumos",
      filtro: resumoNaUnidade,
      inicial: itens => itens[0]?.key,
    },
    {
      grupo: "documento",
      tabs: "tabsDocs",
      pane: "paneDocs",
      src: "srcDocs",
      filtro: docNaUnidade,
      inicial: itens => (itens.find(x => x.inicial) || itens[0])?.key,
    },
  ];

  grupos.forEach(g => {
    const tabsHost = document.getElementById(g.tabs);
    const pane = document.getElementById(g.pane);
    const paneSrc = document.getElementById(g.src);
    if (!tabsHost || !pane) return;

    const itens = (DADOS.resumos || []).filter(r => r.grupo === g.grupo && g.filtro(r));
    const anterior = tabsHost.querySelector('button[aria-selected="true"]');
    const manter = anterior ? anterior.dataset.k : null;
    tabsHost.innerHTML = "";

    const mostrar = k => {
      const r = itens.find(x => x.key === k);
      if (!r) return;
      if (g.grupo === "resumo") RESUMO_ATUAL = r;
      pane.innerHTML = md2html(r.md);
      paneSrc.textContent = "arquivo: " + r.src;
      tabsHost.querySelectorAll("button").forEach(b =>
        b.setAttribute("aria-selected", b.dataset.k === k ? "true" : "false")
      );
    };

    itens.forEach(r => {
      const b = document.createElement("button");
      b.type = "button";
      b.dataset.k = r.key;
      b.textContent = r.title;
      b.setAttribute("role", "tab");
      b.setAttribute("aria-selected", "false");
      b.addEventListener("click", () => mostrar(r.key));
      tabsHost.appendChild(b);
    });

    const escolhida = (manter && itens.some(r => r.key === manter)) ? manter : g.inicial(itens);
    if (escolhida) {
      mostrar(escolhida);
    } else {
      if (g.grupo === "resumo") RESUMO_ATUAL = null;
      pane.innerHTML = `<div class="vazio">Nenhum ${g.grupo} cadastrado para a ${ORDINAL[UN]} unidade ainda.</div>`;
      paneSrc.textContent = "";
    }
  });
}

/* ---------- Modais de Edição Rápida (Zero Tokens) ---------- */
function abrirModal(titulo, htmlCorpo, onMount) {
  const bd = document.getElementById("modalBackdrop");
  document.getElementById("modalTitulo").textContent = titulo;
  const corpo = document.getElementById("modalCorpo");
  corpo.innerHTML = htmlCorpo;
  bd.hidden = false;
  if (onMount) onMount(corpo);
}
function fecharModal() {
  document.getElementById("modalBackdrop").hidden = true;
}
document.getElementById("btnFecharModal")?.addEventListener("click", fecharModal);

// 1. Nova Disciplina
document.getElementById("btnNovaDisciplina")?.addEventListener("click", () => {
  abrirModal("+ Criar Nova Disciplina (Cadeira)", `
    <label><span class="eyebrow">Nome da Disciplina</span>
      <input type="text" id="mDiscNome" placeholder="Ex: Geometria Analítica, Física 1, EDO">
    </label>
    <label><span class="eyebrow">Subtítulo / Turma / Professor</span>
      <input type="text" id="mDiscSub" value="UFPE · 2026.2">
    </label>
    <div class="drawer-actions" style="margin-top:8px">
      <button type="button" class="actbtn primary" id="mBtnCriarDisc">Criar Estrutura da Disciplina</button>
    </div>
  `, el => {
    el.querySelector("#mBtnCriarDisc").addEventListener("click", async () => {
      const nome = el.querySelector("#mDiscNome").value.trim();
      const subtitulo = el.querySelector("#mDiscSub").value.trim();
      if (!nome) return alert("Informe o nome da disciplina.");
      const r = await fetch("/api/disciplinas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nome, subtitulo }),
      });
      const d = await r.json();
      if (!d.ok) return alert(d.erro || "Erro ao criar disciplina.");
      fecharModal();
      DISC = d.pasta;
      UN = 1;
      await carregar();
    });
  });
});

// 2. Editar Cabeçalho / Nota da Unidade
function abrirModalEditarHeader() {
  const u = dadosUnidadeAtual();
  abrirModal(`Editar Cabeçalho — ${u.ordinal} Unidade`, `
    <label><span class="eyebrow">Data da Prova (AAAA-MM-DD)</span>
      <input type="text" id="mHdProva" value="${esc(u.dataProva || "")}" placeholder="2026-11-30">
    </label>
    <label><span class="eyebrow">Subtítulo da Unidade</span>
      <textarea id="mHdSub" rows="3">${esc(u.subtitulo || "")}</textarea>
    </label>
    <label><span class="eyebrow">Tags (uma por linha, ex: Nota: 8,5)</span>
      <textarea id="mHdTags" rows="4">${esc((u.tags || []).join("\n"))}</textarea>
    </label>
    <div class="drawer-actions">
      <button type="button" class="actbtn primary" id="mBtnSalvarHd">Salvar Cabeçalho</button>
    </div>
  `, el => {
    el.querySelector("#mBtnSalvarHd").addEventListener("click", () => {
      u.dataProva = el.querySelector("#mHdProva").value.trim();
      u.subtitulo = el.querySelector("#mHdSub").value.trim();
      u.tags = el.querySelector("#mHdTags").value.split("\n").map(s => s.trim()).filter(Boolean);
      fecharModal();
      salvarCurso(`Atualizar cabeçalho/tags da ${u.ordinal} unidade`);
    });
  });
}

// 3. Adicionar / Editar Tópico em "Onde Estamos"
function abrirModalTopico(idx = null) {
  const u = dadosUnidadeAtual();
  const item = idx !== null ? u.ondeEstamos[idx] : { status: "later", lv: "Em breve", titulo: "", detalhe: "", where: "", secoes: [] };
  abrirModal(idx !== null ? "Editar Tópico" : "+ Adicionar Tópico em Onde Estamos", `
    <div class="form-grid">
      <label><span class="eyebrow">Status</span>
        <select id="mTopStatus">
          <option value="seen" ${item.status === "seen" ? "selected" : ""}>Visto (Aula já dada)</option>
          <option value="next" ${item.status === "next" ? "selected" : ""}>Próxima aula / Em andamento</option>
          <option value="later" ${item.status === "later" ? "selected" : ""}>Depois / Futura</option>
          <option value="prova" ${item.status === "prova" ? "selected" : ""}>Exame / Prova</option>
        </select>
      </label>
      <label><span class="eyebrow">Selo / Data (ex: Visto, Sex 30/10)</span>
        <input type="text" id="mTopLv" value="${esc(item.lv || "")}">
      </label>
    </div>
    <label><span class="eyebrow">Título do Assunto</span>
      <input type="text" id="mTopTit" value="${esc(item.titulo || "")}">
    </label>
    <label><span class="eyebrow">Subtítulo / Detalhes</span>
      <input type="text" id="mTopDet" value="${esc(item.detalhe || "")}">
    </label>
    <div class="form-grid">
      <label><span class="eyebrow">Referência (ex: Stewart 15.4)</span>
        <input type="text" id="mTopWhere" value="${esc(item.where || "")}">
      </label>
      <label><span class="eyebrow">Seções p/ Destravar Automático (separadas por vírgula)</span>
        <input type="text" id="mTopSecoes" value="${esc((item.secoes || []).join(", "))}" placeholder="15.4, L5">
      </label>
    </div>
    <div class="drawer-actions">
      <button type="button" class="actbtn primary" id="mBtnSalvarTop">Salvar Tópico</button>
    </div>
  `, el => {
    el.querySelector("#mBtnSalvarTop").addEventListener("click", () => {
      const novo = {
        status: el.querySelector("#mTopStatus").value,
        lv: el.querySelector("#mTopLv").value.trim() || "Visto",
        titulo: el.querySelector("#mTopTit").value.trim(),
        detalhe: el.querySelector("#mTopDet").value.trim(),
        where: el.querySelector("#mTopWhere").value.trim(),
        secoes: el.querySelector("#mTopSecoes").value.split(",").map(s => s.trim()).filter(Boolean),
      };
      if (!novo.titulo) return alert("Informe o título do tópico.");
      u.ondeEstamos = u.ondeEstamos || [];
      if (idx !== null) u.ondeEstamos[idx] = novo; else u.ondeEstamos.push(novo);
      fecharModal();
      const destravar = novo.status === "seen" ? novo.secoes : [];
      salvarCurso(`Salvar tópico '${novo.titulo}'`, destravar);
    });
  });
}
document.getElementById("btnAddTopico")?.addEventListener("click", () => abrirModalTopico(null));

// 4. Adicionar / Editar Sessão no Cronograma
function abrirModalSessaoCrono(fIdx = 0, lIdx = null) {
  const u = dadosUnidadeAtual();
  if (!u.fases || !u.fases.length) {
    u.fases = [{ estilo: "f1", eyebrow: "Plano de estudo", titulo: "Cronograma", tag: "ativo", colunas: ["Sessão", "Data", "Foco", "Exercícios"], linhas: [] }];
  }
  const fase = u.fases[fIdx] || u.fases[0];
  const ln = lIdx !== null ? fase.linhas[lIdx] : { feito: false, s: `S${(fase.linhas?.length || 0) + 1}`, d: "", t: "", x: [""] };
  abrirModal(lIdx !== null ? `Editar Sessão ${ln.s}` : "+ Nova Sessão no Cronograma", `
    <div class="form-grid">
      <label><span class="eyebrow">Código (ex: S1, P1)</span>
        <input type="text" id="mCrS" value="${esc(ln.s || "")}">
      </label>
      <label><span class="eyebrow">Data (ex: sáb 31/10)</span>
        <input type="text" id="mCrD" value="${esc(ln.d || "")}">
      </label>
    </div>
    <label><span class="eyebrow">Foco da Sessão (aceita HTML básico)</span>
      <input type="text" id="mCrT" value="${esc(ln.t || "")}" placeholder="<strong>15.4 Integrais em polares</strong>">
    </label>
    <label><span class="eyebrow">Colunas de Exercícios (separe colunas por | )</span>
      <input type="text" id="mCrX" value="${esc((ln.x || []).join(" | "))}" placeholder="15.4: 11, 29 | L5 #6(a), #7">
    </label>
    <div class="drawer-actions">
      <button type="button" class="actbtn primary" id="mBtnSalvarCr">Salvar Sessão</button>
    </div>
  `, el => {
    el.querySelector("#mBtnSalvarCr").addEventListener("click", () => {
      const novaLinha = {
        feito: Boolean(ln.feito),
        s: el.querySelector("#mCrS").value.trim(),
        d: el.querySelector("#mCrD").value.trim(),
        t: el.querySelector("#mCrT").value.trim(),
        x: el.querySelector("#mCrX").value.split("|").map(s => s.trim()),
      };
      if (lIdx !== null) fase.linhas[lIdx] = novaLinha; else fase.linhas.push(novaLinha);
      fecharModal();
      salvarCurso(`Salvar sessão ${novaLinha.s} no cronograma`);
    });
  });
}
document.getElementById("btnAddSessaoCrono")?.addEventListener("click", () => {
  const u = dadosUnidadeAtual();
  const idxPlano = (u.fases || []).findIndex(f => (f.linhas || []).length > 4);
  abrirModalSessaoCrono(idxPlano >= 0 ? idxPlano : 0, null);
});

// 5. Adicionar / Editar Fórmula no Formulário
function abrirModalFormula(idx = null) {
  const u = dadosUnidadeAtual();
  const card = idx !== null ? u.formulario[idx] : { titulo: "", fml: "", notas: [] };
  abrirModal(idx !== null ? "Editar Fórmula" : "+ Novo Cartão no Formulário", `
    <label><span class="eyebrow">Título do Cartão</span>
      <input type="text" id="mFmTit" value="${esc(card.titulo || "")}" placeholder="Ex: Mudança para Coordenadas Esféricas">
    </label>
    <label><span class="eyebrow">Fórmula / Receita (Monoespaçado)</span>
      <textarea id="mFmCode" class="mono" rows="5">${esc(card.fml || "")}</textarea>
    </label>
    <label><span class="eyebrow">Observações / Armadilhas de Prova (uma por linha)</span>
      <textarea id="mFmNotas" rows="3">${esc((card.notas || []).join("\n"))}</textarea>
    </label>
    <div class="drawer-actions">
      <button type="button" class="actbtn primary" id="mBtnSalvarFm">Salvar no Formulário</button>
    </div>
  `, el => {
    el.querySelector("#mBtnSalvarFm").addEventListener("click", () => {
      const novo = {
        titulo: el.querySelector("#mFmTit").value.trim(),
        fml: el.querySelector("#mFmCode").value,
        notas: el.querySelector("#mFmNotas").value.split("\n").map(s => s.trim()).filter(Boolean),
      };
      if (!novo.titulo || !novo.fml) return alert("Preencha o título e a fórmula.");
      u.formulario = u.formulario || [];
      if (idx !== null) u.formulario[idx] = novo; else u.formulario.push(novo);
      fecharModal();
      salvarCurso(`Salvar fórmula '${novo.titulo}'`);
    });
  });
}
document.getElementById("btnNovaFormula")?.addEventListener("click", () => abrirModalFormula(null));

// 6. Gerador Rápido de Lista / Seção (1..15 + Extrator de PDF Local)
document.getElementById("btnNovaLista")?.addEventListener("click", () => {
  const pdfOpts = (DADOS?.arquivosPdf || [])
    .map(p => `<option value="${esc(p.caminho)}">${esc(p.grupo + "/" + p.nome)}</option>`)
    .join("");
  abrirModal("+ Nova Lista ou Seção de Exercícios (Zero Tokens)", `
    <div class="form-grid three">
      <label><span class="eyebrow">Código (ex: L7, 15.6)</span>
        <input type="text" id="mExSec" placeholder="L7">
      </label>
      <label><span class="eyebrow">Unidade</span>
        <select id="mExUn">
          <option value="1" ${UN === 1 ? "selected" : ""}>1ª unidade</option>
          <option value="2" ${UN === 2 ? "selected" : ""}>2ª unidade</option>
          <option value="3" ${UN === 3 ? "selected" : ""}>3ª unidade</option>
        </select>
      </label>
      <label><span class="eyebrow">Vincular PDF da Pasta</span>
        <select id="mExPdf"><option value="">— Nenhum —</option>${pdfOpts}</select>
      </label>
    </div>
    <label><span class="eyebrow">Título da Lista / Seção</span>
      <input type="text" id="mExNome" placeholder="Ex: Lista 7 — Revisão para a Prova">
    </label>
    <div class="form-grid">
      <label><span class="eyebrow">Questões Linha 1 — Prioridade (ex: 1..5, *6, 8a, 8b)</span>
        <input type="text" id="mExL1" placeholder="1..10, *11, *12">
      </label>
      <label><span class="eyebrow">Questões Linha 2 — Reforço (opcional)</span>
        <input type="text" id="mExL2" placeholder="13..18">
      </label>
    </div>
    <div class="anexo-box">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap">
        <span class="eyebrow">Opcional: Extrair enunciados automaticamente do PDF selecionado (pdfplumber local)</span>
        <button type="button" class="actbtn small" id="mBtnExtrairExPdf">⚡ Extrair Enunciados do PDF</button>
      </div>
      <div id="mExExtraidosInfo" class="mono" style="font-size:11.5px;margin-top:6px;color:var(--muted)"></div>
    </div>
    <div class="drawer-actions">
      <button type="button" class="actbtn primary" id="mBtnCriarLista">Criar Lista Marcável (✓ / ✗ / ?)</button>
    </div>
  `, el => {
    let itensExtraidos = null;
    el.querySelector("#mBtnExtrairExPdf").addEventListener("click", async () => {
      const arq = el.querySelector("#mExPdf").value;
      if (!arq) return alert("Selecione primeiro um PDF no campo 'Vincular PDF da Pasta'.");
      const info = el.querySelector("#mExExtraidosInfo");
      info.textContent = "Lendo PDF localmente com pdfplumber…";
      const r = await fetch("/api/extrair-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ disciplina: DISC, arquivo: arq, pgInicio: 1, pgFim: 6 }),
      });
      const d = await r.json();
      if (d.questoesDetectadas && d.questoesDetectadas.length) {
        itensExtraidos = d.questoesDetectadas;
        info.textContent = `✓ ${itensExtraidos.length} questões com enunciado detectadas automaticamente! Clique em Criar Lista abaixo.`;
      } else {
        info.textContent = "Nenhuma questão numerada padrão detectada; usaremos os números digitados nos campos acima.";
      }
    });

    el.querySelector("#mBtnCriarLista").addEventListener("click", async () => {
      const sec = el.querySelector("#mExSec").value.trim();
      const nome = el.querySelector("#mExNome").value.trim();
      const un = Number(el.querySelector("#mExUn").value);
      const pdf = el.querySelector("#mExPdf").value;
      const l1Numeros = el.querySelector("#mExL1").value.trim();
      const l2Numeros = el.querySelector("#mExL2").value.trim();
      if (!sec || !nome) return alert("Preencha o código e o título da lista.");
      const payload = {
        disciplina: DISC,
        acao: "criar_secao_rapida",
        sec,
        nome,
        un,
        pdf,
        l1Numeros: l1Numeros || (itensExtraidos ? "" : "1..10"),
        l2Numeros,
      };
      if (itensExtraidos && !l1Numeros) payload.l1Itens = itensExtraidos;
      const r = await fetch("/api/exercicios", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const d = await r.json();
      if (!d.ok) return alert(d.erro || "Erro ao criar lista.");
      fecharModal();
      UN = un;
      await carregar();
    });
  });
});

// 7. Criar / Editar Resumo ou Resolução em Markdown
function abrirModalMarkdown(tipo, nomeInicial = "", conteudoInicial = "") {
  const ehRes = tipo === "resumo";
  abrirModal(ehRes ? "Salvar / Editar Resumo (.md em resumos/)" : `Salvar / Editar Resolução (${nomeInicial})`, `
    <label><span class="eyebrow">${ehRes ? "Nome do Arquivo em resumos/ (ex: 08-integrais-polares.md)" : "ID do Exercício (ex: 15.4-22 ou L5-5)"}</span>
      <input type="text" id="mMdNome" value="${esc(nomeInicial)}" placeholder="${ehRes ? "08-integrais-polares.md" : "15.4-22"}">
    </label>
    <label><span class="eyebrow">Conteúdo Markdown</span>
      <textarea id="mMdTexto" class="mono skill-editor" rows="14">${esc(conteudoInicial)}</textarea>
    </label>
    <div class="drawer-actions">
      <button type="button" class="actbtn primary" id="mBtnSalvarMd">💾 Salvar Arquivo Markdown</button>
    </div>
  `, el => {
    el.querySelector("#mBtnSalvarMd").addEventListener("click", async () => {
      const nomeArquivo = el.querySelector("#mMdNome").value.trim();
      const conteudo = el.querySelector("#mMdTexto").value;
      if (!nomeArquivo || !conteudo.trim()) return alert("Preencha o nome e o conteúdo.");
      const r = await fetch("/api/markdown", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ disciplina: DISC, tipo, nomeArquivo, conteudo }),
      });
      const d = await r.json();
      if (!d.ok) return alert(d.erro || "Erro ao salvar arquivo.");
      fecharModal();
      await carregar();
    });
  });
}

document.getElementById("btnColarResumo")?.addEventListener("click", () => {
  const qtd = (DADOS?.resumos || []).filter(r => r.grupo === "resumo").length;
  const prefixo = String(qtd).padStart(2, "0") + "-novo-resumo.md";
  abrirModalMarkdown("resumo", prefixo, `# Novo Resumo\n\n> Referência · ${ORDINAL[UN]} unidade\n\n## 1. Definição\n\n`);
});

document.getElementById("btnEditarResumoAtual")?.addEventListener("click", () => {
  if (!RESUMO_ATUAL) return alert("Nenhum resumo selecionado.");
  abrirModalMarkdown("resumo", RESUMO_ATUAL.key + ".md", RESUMO_ATUAL.md);
});

/* ---------- Desfazer (Undo) e Reler Pasta ---------- */
document.getElementById("btnUndo")?.addEventListener("click", async () => {
  const r = await fetch("/api/undo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ disciplina: DISC }),
  });
  const d = await r.json();
  if (!d.ok) return alert(d.erro || "Nada para desfazer.");
  await carregar();
});
document.getElementById("btnRelerPasta")?.addEventListener("click", carregar);

/* ---------- Drawer do Agente, RAG em 2 Níveis e Skills ---------- */
const drawerBackdrop = document.getElementById("drawerBackdrop");
function abrirDrawer(aba = "agente") {
  drawerBackdrop.hidden = false;
  selecionarAbaDrawer(aba);
}
function fecharDrawer() {
  drawerBackdrop.hidden = true;
}
document.getElementById("btnAbrirAgente")?.addEventListener("click", () => abrirDrawer("agente"));
document.getElementById("btnFecharAgente")?.addEventListener("click", fecharDrawer);

function selecionarAbaDrawer(qual) {
  document.querySelectorAll(".drawer-tabs button").forEach(b => {
    const ativo = b.dataset.dtab === qual;
    b.setAttribute("aria-selected", ativo ? "true" : "false");
  });
  ["agente", "rag", "skills"].forEach(k => {
    const el = document.getElementById("dtab-" + k);
    if (el) el.hidden = k !== qual;
  });
  if (qual === "rag") carregarStatusRag();
}
document.querySelectorAll(".drawer-tabs button").forEach(b =>
  b.addEventListener("click", () => selecionarAbaDrawer(b.dataset.dtab))
);

function popularDrawerAgente() {
  if (!DADOS) return;
  const skills = DADOS.skills || [];
  const selAg = document.getElementById("agSkill");
  const selEd = document.getElementById("selSkillEdit");
  if (selAg) {
    const manter = selAg.value;
    selAg.innerHTML = "";
    skills.filter(s => s.escopo === "global").forEach(s => {
      const o = document.createElement("option");
      o.value = s.id;
      o.textContent = `${s.title} (${s.id})`;
      selAg.appendChild(o);
    });
    if (manter && Array.from(selAg.options).some(o => o.value === manter)) selAg.value = manter;
  }
  if (selEd) {
    const manterEd = selEd.value;
    selEd.innerHTML = "";
    skills.forEach(s => {
      const o = document.createElement("option");
      o.value = s.id;
      o.textContent = `[${s.escopo.toUpperCase()}] ${s.title} (${s.arquivo})`;
      selEd.appendChild(o);
    });
    if (manterEd && Array.from(selEd.options).some(o => o.value === manterEd)) selEd.value = manterEd;
    atualizarEditorSkill();
  }

  // PDFs no seletor de anexo do Agente
  const pdfSel = document.getElementById("agPdfSelect");
  if (pdfSel) {
    pdfSel.innerHTML = `<option value="">— Nenhum —</option>`;
    (DADOS.arquivosPdf || []).forEach(p => {
      const o = document.createElement("option");
      o.value = p.caminho;
      o.textContent = `${p.grupo}/${p.nome}`;
      pdfSel.appendChild(o);
    });
  }

  // Status da API Key
  const stKey = document.getElementById("cfgKeyStatus");
  if (stKey && DADOS.configAgente) {
    stKey.textContent = DADOS.configAgente.temApiKey
      ? `✓ Chave configurada (${DADOS.configAgente.apiKeyMascarada})`
      : "Sem chave configurada (usando modo Pacote RAG Offline por padrão)";
  }
}

function atualizarEditorSkill() {
  const id = document.getElementById("selSkillEdit")?.value;
  const sk = (DADOS?.skills || []).find(s => s.id === id);
  const txt = document.getElementById("txtSkillConteudo");
  if (txt && sk) txt.value = sk.conteudo;
}
document.getElementById("selSkillEdit")?.addEventListener("change", atualizarEditorSkill);

// Atalhos rápidos na página que abrem o Agente já parametrizado
function abrirAgenteParaExercicio(sec, num, nivel) {
  abrirDrawer("agente");
  document.getElementById("agSkill").value = "tutor-progressivo";
  document.getElementById("agSecao").value = sec;
  document.getElementById("agNumero").value = num;
  document.getElementById("agNivel").value = nivel;
  document.getElementById("btnRodarAgente").click();
}

document.getElementById("btnGerarResumoIA")?.addEventListener("click", () => {
  abrirDrawer("agente");
  document.getElementById("agSkill").value = "resumidor-aula";
  const primSec = secoesDaUnidade()[0]?.sec || "15.4";
  document.getElementById("agSecao").value = primSec;
  document.getElementById("agNumero").value = "";
});

document.getElementById("btnRevisarErrosIA")?.addEventListener("click", () => {
  abrirDrawer("agente");
  document.getElementById("agSkill").value = "estrategista-revisao";
  document.getElementById("btnRodarAgente").click();
});

// Extrair texto de PDF no painel do Agente
document.getElementById("btnExtrairPdfAgente")?.addEventListener("click", async () => {
  const arq = document.getElementById("agPdfSelect").value;
  if (!arq) return alert("Escolha um PDF primeiro.");
  const pgInicio = Number(document.getElementById("agPdfIni").value || 1);
  const pgFim = Number(document.getElementById("agPdfFim").value || 3);
  const r = await fetch("/api/extrair-pdf", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ disciplina: DISC, arquivo: arq, pgInicio, pgFim }),
  });
  const d = await r.json();
  if (d.erro) return alert(d.erro);
  document.getElementById("agTextoAnexo").value = d.textoExtraido || "";
});

async function lerImagensBase64() {
  const input = document.getElementById("agImgsInput");
  if (!input || !input.files || !input.files.length) return [];
  const lista = [];
  for (const f of Array.from(input.files).slice(0, 5)) {
    const b64 = await new Promise(res => {
      const reader = new FileReader();
      reader.onload = () => res(String(reader.result).split(",")[1] || "");
      reader.readAsDataURL(f);
    });
    if (b64) lista.push({ mimeType: f.type || "image/png", data: b64 });
  }
  return lista;
}

// Executar Agente (Multi-Busca RAG + Function Calling)
document.getElementById("btnRodarAgente")?.addEventListener("click", async () => {
  const btn = document.getElementById("btnRodarAgente");
  const skill = document.getElementById("agSkill").value;
  const [modo, modelo] = document.getElementById("agModoModelo").value.split(":");
  const secao = document.getElementById("agSecao").value.trim();
  const numero = document.getElementById("agNumero").value.trim();
  const nivel = document.getElementById("agNivel").value;
  const mensagem = document.getElementById("agMensagem").value.trim();
  const textoAnexo = document.getElementById("agTextoAnexo").value.trim();
  const imagensBase64 = await lerImagensBase64();

  const wrap = document.getElementById("agResultadoWrap");
  const outMd = document.getElementById("agOutputMd");
  const telBar = document.getElementById("agTelemetria");
  const toolsList = document.getElementById("agToolsList");
  const copyBar = document.getElementById("agCopyBar");
  const cronoProp = document.getElementById("agCronoProposta");

  wrap.hidden = false;
  btn.disabled = true;
  btn.textContent = "⏳ Executando Multi-Busca no RAG…";
  outMd.innerHTML = "<p>Consultando banco RAG estruturado e processando Skill…</p>";
  toolsList.innerHTML = "";
  copyBar.hidden = true;
  cronoProp.hidden = true;

  try {
    const r = await fetch("/api/agente/executar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        disciplina: DISC,
        skill,
        modo,
        modelo,
        secao,
        numero,
        nivel,
        unidade: UN,
        mensagem,
        textoAnexo,
        imagensBase64,
      }),
    });
    const d = await r.json();
    if (!d.ok) {
      outMd.innerHTML = `<p style="color:var(--err)"><b>Erro:</b> ${esc(d.erro || "Falha desconhecida")}</p>`;
      return;
    }

    const tel = d.telemetria || {};
    const tools = tel.toolsExecutadas || [];
    telBar.innerHTML = `
      <span><b>Modelo:</b> ${esc(tel.modelo || modo)}</span>
      <span><b>Multi-Buscas / Tools:</b> ${tools.length} chamada(s)</span>
      <span><b>Tokens:</b> ${tel.totalTokens || 0} total (${tel.inputTokens || 0} in / ${tel.outputTokens || 0} out)</span>
    `;

    toolsList.innerHTML = tools.map((t, idx) => `
      <div class="tool-pill">
        <span><b>#${idx + 1} ${esc(t.tool)}</b>(${esc(JSON.stringify(t.args || {}))})</span>
        <span>${t.tempoMs} ms · ${t.charsRetorno} chars</span>
      </div>
    `).join("");

    if (d.promptEmpacotado) {
      ULTIMO_PROMPT_RAG = d.promptEmpacotado;
      copyBar.hidden = false;
    }

    if (d.propostasCronograma && d.propostasCronograma.length) {
      const prop = d.propostasCronograma[0];
      cronoProp.hidden = false;
      cronoProp.className = "crono-prop-card";
      cronoProp.innerHTML = `
        <strong>📅 Proposta de Ajuste no Cronograma (${prop.unidade}ª unidade)</strong>
        <p style="font-size:13px;margin:4px 0 8px">${esc(prop.motivo)}</p>
        <button type="button" class="actbtn primary small" id="btnConfirmarCronoAgente">✓ Confirmar e Aplicar no Cronograma</button>
      `;
      cronoProp.querySelector("#btnConfirmarCronoAgente")?.addEventListener("click", () => {
        const uAlvo = CURSO.unidades[String(prop.unidade)];
        if (uAlvo && uAlvo.fases && uAlvo.fases.length) {
          const fPlano = uAlvo.fases.find(f => (f.linhas || []).length > 3) || uAlvo.fases[0];
          (prop.sessoes || []).forEach(s => fPlano.linhas.push({ feito: false, s: s.s, d: s.d, t: s.t, x: s.x || ["—"] }));
          cronoProp.hidden = true;
          salvarCurso("Aplicar ajuste de cronograma sugerido pelo Agente");
        }
      });
    }

    const avisoHtml = d.avisoSemChave ? `<p class="note" style="margin-bottom:12px"><b>Nota:</b> ${esc(d.avisoSemChave)}</p>` : "";
    outMd.innerHTML = avisoHtml + md2html(d.respostaMarkdown || "");

    if (d.arquivosSalvos && d.arquivosSalvos.length) {
      await carregar();
    }
  } catch (e) {
    outMd.innerHTML = `<p style="color:var(--err)">Erro de conexão: ${esc(e.message)}</p>`;
  } finally {
    btn.disabled = false;
    btn.textContent = "▶ Executar Agente com Multi-Busca no RAG";
  }
});

document.getElementById("btnCopiarPromptRag")?.addEventListener("click", async () => {
  if (!ULTIMO_PROMPT_RAG) return;
  await navigator.clipboard.writeText(ULTIMO_PROMPT_RAG);
  const b = document.getElementById("btnCopiarPromptRag");
  b.textContent = "✓ Prompt RAG Copiado!";
  setTimeout(() => { b.textContent = "📋 Copiar Prompt RAG Completo"; }, 2000);
});

document.getElementById("btnAbrirColarMd")?.addEventListener("click", () => {
  const sk = document.getElementById("agSkill").value;
  const sec = document.getElementById("agSecao").value.trim() || "15.4";
  const num = document.getElementById("agNumero").value.trim() || "22";
  if (sk === "resumidor-aula") {
    abrirModalMarkdown("resumo", `08-resumo-${sec.replace(".", "-")}.md`, "");
  } else {
    abrirModalMarkdown("resolucao", `${sec}-${num}`, "");
  }
});

// Aba 2: Explorador do RAG
async function carregarStatusRag() {
  const bar = document.getElementById("ragStatsBar");
  if (!bar) return;
  const r = await fetch("/api/rag/status?disciplina=" + encodeURIComponent(DISC));
  const d = await r.json();
  bar.textContent = `Banco SQLite FTS5 ativo · ${d.totalUnidadesFts || 0} unidades lógicas indexadas · ${d.secoesLivroEmCache || 0} seções completas de livros em cache (${d.tempoMs || 0} ms)`;
}

document.getElementById("btnBuscarRag")?.addEventListener("click", async () => {
  const modoBusca = document.getElementById("ragModo").value;
  const q = document.getElementById("ragQuery").value.trim();
  const secOuNum = document.getElementById("ragSecaoOuNum").value.trim();
  const pre = document.getElementById("ragResultadoPre");
  pre.textContent = "Consultando SQLite FTS5…";
  const payload = {
    disciplina: DISC,
    modoBusca,
    consulta: q,
    secao: modoBusca === "fts" ? secOuNum : (q || "15.4"),
    numero: secOuNum || "22",
    livro: "stewart",
  };
  const r = await fetch("/api/rag/buscar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const d = await r.json();
  pre.textContent = JSON.stringify(d, null, 2);
  carregarStatusRag();
});

document.getElementById("btnReindexarRag")?.addEventListener("click", async () => {
  const pre = document.getElementById("ragResultadoPre");
  pre.textContent = "Reindexando todos os arquivos da disciplina…";
  const r = await fetch("/api/rag/reindexar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ disciplina: DISC }),
  });
  const d = await r.json();
  pre.textContent = "Índice reconstruído com sucesso:\n" + JSON.stringify(d, null, 2);
  carregarStatusRag();
});

// Aba 3: Salvar API Key e Skills (.md)
document.getElementById("btnSalvarApiKey")?.addEventListener("click", async () => {
  const apiKey = document.getElementById("cfgApiKey").value.trim();
  const r = await fetch("/api/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ apiKey }),
  });
  const d = await r.json();
  document.getElementById("cfgApiKey").value = "";
  if (DADOS) DADOS.configAgente = d;
  popularDrawerAgente();
  alert("Configuração da API salva localmente!");
});

document.getElementById("btnSalvarSkill")?.addEventListener("click", async () => {
  const id = document.getElementById("selSkillEdit").value;
  const conteudo = document.getElementById("txtSkillConteudo").value;
  const sk = (DADOS?.skills || []).find(s => s.id === id);
  const r = await fetch("/api/skills", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      disciplina: DISC,
      id,
      escopo: sk?.escopo || "global",
      conteudo,
    }),
  });
  const d = await r.json();
  if (!d.ok) return alert(d.erro || "Erro ao salvar Skill.");
  await carregar();
  alert(`Skill '${id}' salva com sucesso!`);
});

document.getElementById("btnNovaSkill")?.addEventListener("click", async () => {
  const nome = prompt("Identificador da nova Skill (ex: gerador-simulado):");
  if (!nome) return;
  const template = `---\nname: ${nome}\ntitle: ${nome}\ndescription: Skill personalizada\ndefault_model: gemini-3.8-flash\n---\n\n# Skill: ${nome}\n\nDescreva aqui o fluxo de buscas no RAG e o formato de saída esperado.\n`;
  await fetch("/api/skills", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ disciplina: DISC, id: nome, escopo: "global", conteudo: template }),
  });
  await carregar();
  document.getElementById("selSkillEdit").value = nome;
  atualizarEditorSkill();
});

/* ---------- Descarga imediata ao fechar a aba ---------- */
function descarregar() {
  if (!salvarTimer) return;
  clearTimeout(salvarTimer);
  salvarTimer = null;
  const corpo = JSON.stringify({ disciplina: DISC, marcacoes: STATUS });
  try {
    if (navigator.sendBeacon) {
      navigator.sendBeacon("/api/status", new Blob([corpo], { type: "application/json" }));
      return;
    }
  } catch (e) {}
}
window.addEventListener("pagehide", descarregar);

carregar();
