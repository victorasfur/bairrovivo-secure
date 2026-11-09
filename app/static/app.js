const CATEGORIAS = {
  buraco: ["Buraco / pavimento", "#f87171"],
  iluminacao: ["Iluminação", "#fbbf24"],
  descarte: ["Descarte irregular", "#a78bfa"],
  calcada: ["Calçada / acessibilidade", "#38bdf8"],
  mobiliario: ["Mobiliário urbano", "#34d399"],
};
const STATUS = {
  recebida: "Recebida", em_analise: "Em análise", encaminhada: "Encaminhada",
  em_atendimento: "Em atendimento", resolvida: "Resolvida", nao_procedente: "Não procedente",
};

const $ = (id) => document.getElementById(id);
const mapa = L.map("mapa").setView([-23.5894, -46.6342], 15);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19, attribution: "&copy; OpenStreetMap",
}).addTo(mapa);
const camada = L.layerGroup().addTo(mapa);
let escolhido = null, marcadorEscolhido = null;

function preencherSelects() {
  for (const [k, [nome]] of Object.entries(CATEGORIAS)) {
    $("f-categoria").add(new Option(nome, k));
    $("f-nova-categoria").add(new Option(nome, k));
  }
  for (const [k, nome] of Object.entries(STATUS)) $("f-status").add(new Option(nome, k));
}

function el(tag, texto, cls) {
  const e = document.createElement(tag);
  if (texto !== undefined) e.textContent = texto;
  if (cls) e.className = cls;
  return e;
}

async function carregarKpis() {
  const r = await (await fetch("/api/resumo")).json();
  const caixa = $("kpis");
  caixa.replaceChildren();
  const abertas = r.total - r.por_status.resolvida - r.por_status.nao_procedente;
  const itens = [["Total", r.total], ["Abertas", abertas], ["Resolvidas", r.por_status.resolvida]];
  for (const [k, [nome]] of Object.entries(CATEGORIAS)) itens.push([nome, r.por_categoria[k]]);
  for (const [nome, valor] of itens) {
    const k = el("div", undefined, "kpi");
    k.append(el("b", String(valor)), el("span", nome));
    caixa.append(k);
  }
}

async function carregarOcorrencias() {
  const p = new URLSearchParams();
  if ($("f-categoria").value) p.set("categoria", $("f-categoria").value);
  if ($("f-status").value) p.set("status", $("f-status").value);
  const dados = await (await fetch("/api/ocorrencias?" + p)).json();
  camada.clearLayers();
  const lista = $("lista");
  lista.replaceChildren();
  for (const o of dados) {
    const [nomeCat, cor] = CATEGORIAS[o.categoria];
    L.circleMarker([o.latitude, o.longitude], { radius: 7, color: cor, fillOpacity: 0.7 })
      .bindPopup(`${o.titulo} (${STATUS[o.status]})`).addTo(camada);
    const li = el("li");
    li.append(el("strong", o.titulo), el("small", o.descricao));
    li.append(el("br"), el("span", nomeCat, "tag"), el("span", STATUS[o.status], "tag"));
    li.append(el("span", o.origem === "sintetico" ? "fictício" : "cidadão", o.origem === "sintetico" ? "tag fict" : "tag"));
    lista.append(li);
  }
}

mapa.on("click", (e) => {
  escolhido = e.latlng;
  if (marcadorEscolhido) marcadorEscolhido.remove();
  marcadorEscolhido = L.marker(e.latlng).addTo(mapa);
  $("local").textContent = `Local: ${e.latlng.lat.toFixed(5)}, ${e.latlng.lng.toFixed(5)}`;
});

$("form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const msg = $("msg");
  if (!escolhido) { msg.textContent = "Escolha o local clicando no mapa."; return; }
  const f = new FormData(ev.target);
  const corpo = {
    titulo: f.get("titulo"), categoria: f.get("categoria"), descricao: f.get("descricao") || "",
    alias: f.get("alias") || "anônimo", latitude: escolhido.lat, longitude: escolhido.lng,
  };
  const r = await fetch("/api/ocorrencias", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(corpo),
  });
  if (r.ok) {
    msg.textContent = "Ocorrência registrada! Status: Recebida.";
    ev.target.reset();
    await Promise.all([carregarOcorrencias(), carregarKpis()]);
  } else {
    msg.textContent = "Não foi possível registrar. Confira título (mín. 5 letras) e categoria.";
  }
});

$("f-categoria").addEventListener("change", carregarOcorrencias);
$("f-status").addEventListener("change", carregarOcorrencias);

preencherSelects();
carregarKpis();
carregarOcorrencias();
