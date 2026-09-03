import { writeFileSync, readFileSync } from "node:fs";

// @font-face local (caminhos relativos à raiz do projeto)
let FONT_CSS = "";
try {
  FONT_CSS = readFileSync(new URL("./assets/fonts/fonts.css", import.meta.url), "utf8")
    .replace(/\.\/fonts\//g, "assets/fonts/");
} catch (e) {
  console.log("Aviso: fonts.css não encontrado, usando fontes padrão.");
}

// Formato: padrão 16:9; passe --vertical para 9:16 (Shorts)
const VERT = process.argv.includes("--vertical");
const W = VERT ? 1080 : 1920;
const H = VERT ? 1920 : 1080;
const OUT = "index.html"; // sempre index.html

const AUDIO = [5.0, 1.621, 2.496, 1.92, 2.069, 2.411, 2.155, 1.515, 5.077];
const LEAD = 0.5;   // visual estabelece antes da voz
const TAIL = 0.9;   // segura depois da voz
const FADE = 0.45;

// Timing por cena
let t = 0;
const S = AUDIO.map((a, i) => {
  const dur = LEAD + a + TAIL;
  const o = { i: i + 1, start: round(t), dur: round(dur), audioStart: round(t + LEAD), audioDur: round(a), end: round(t + dur) };
  t += dur;
  return o;
});
const TOTAL = round(t);
function round(n) { return Math.round(n * 1000) / 1000; }

const CAPTIONS = ["O desconhecido", "Amor sem limites", "João 3:16", "Amor eterno", "Transformação", "Escuridão", "Força renovada", "Salvação", "Mais conteúdo em inema.club"];

// ---------- CONTEÚDO HTML POR CENA ----------
function scene1() {
  return `<div class='grid2'><div class='left'><div id='s1-background' class='accent2'></div></div><div class='right'><div class='eyebrow'>GANCHO BOMBASTICO</div><h1 id='s1-title' class='title'>O Segredo de Jesus Cristo</h1><p id='s1-sub' class='lead'>Você está pronto para descobrir o segredo que pode mudar sua vida?</p></div></div>`;
}
function scene2() {
  return `<div class='grid2'><div class='left'><div id='s2-background' class='accent'></div></div><div class='right'><div class='eyebrow'>A VERDADE OCULTA</div><h1 id='s2-title' class='title'>Deus deu tudo por você</h1><p id='s2-sub' class='lead'>O amor sem limites</p></div></div>`;
}
function scene3() {
  return `<div class='grid2'><div class='left'><div id='s3-background' class='dim'></div></div><div class='right'><div class='eyebrow'>A PROVA DAS ESCRITURAS</div><h1 id='s3-title' class='title'>João 3:16: Deus deu o seu Filho</h1><p id='s3-sub' class='lead'>A palavra de Deus</p></div></div>`;
}
function scene4() {
  return `<div class='grid2'><div class='left'><div id='s4-background' class='accent2'></div></div><div class='right'><div class='eyebrow'>O MISTÉRIO REVELADO</div><h1 id='s4-title' class='title'>O amor de Deus vence a morte</h1><p id='s4-sub' class='lead'>A vitória eterna</p></div></div>`;
}
function scene5() {
  return `<div class='grid2'><div class='left'><div id='s5-background' class='accent'></div></div><div class='right'><div class='eyebrow'>A TRANSFORMAÇÃO</div><h1 id='s5-title' class='title'>Tudo muda quando você ama a Deus</h1><p id='s5-sub' class='lead'>A transformação interior</p></div></div>`;
}
function scene6() {
  return `<div class='grid2'><div class='left'><div id='s6-background' class='dim'></div></div><div class='right'><div class='eyebrow'>O CONFRONTO</div><h1 id='s6-title' class='title'>Ignorar a verdade é caminhar na escuridão</h1><p id='s6-sub' class='lead'>A escolha é sua</p></div></div>`;
}
function scene7() {
  return `<div class='grid2'><div class='left'><div id='s7-background' class='accent2'></div></div><div class='right'><div class='eyebrow'>O TESTEMUNHO</div><h1 id='s7-title' class='title'>A esperança no Senhor renova forças</h1><p id='s7-sub' class='lead'>A força renovada</p></div></div>`;
}
function scene8() {
  return `<div class='grid2'><div class='left'><div id='s8-background' class='accent'></div></div><div class='right'><div class='eyebrow'>O CHAMADO</div><h1 id='s8-title' class='title'>Cristo é sua salvação</h1><p id='s8-sub' class='lead'>A salvação eterna</p></div></div>`;
}


function scene9() {
  return `
    <div class="cta-eyebrow" id="s9-eye">CONTINUA EM</div>
    <div class="cta-brand" id="s9-brand"><span class="b1">INEMA</span><span class="bdotsep">.</span><span class="b2">CLUB</span></div>
    <div class="rule center" id="s9-rule"></div>
    <div class="cta-url mono"><span class="cta-globe">🌐</span>inema.club</div>
    <div class="reg tl" id="s9-r1"></div><div class="reg br" id="s9-r2"></div>`;
}

const BODIES = [scene1, scene2, scene3, scene4, scene5, scene6, scene7, scene8, scene9];

// ---------- ANIMAÇÃO POR CENA (retorna código GSAP, t = início absoluto) ----------
function anim(i, t) {
  const e = (sel) => JSON.stringify(sel);
  const L = [];
  const P = (s) => L.push(s);
  // entrada/saída do inner (comum)
  P(`tl.fromTo("#scene-inner-${i}",{opacity:0},{opacity:1,duration:${FADE},ease:"power2.out"},${t});`);
  P(`tl.to("#scene-inner-${i}",{opacity:0,duration:${FADE},ease:"power2.in"},${round(S[i-1].end - FADE)});`);
  P(`tl.set("#scene-inner-${i}",{opacity:0},${round(S[i-1].end)});`);
  const at = (d) => round(t + d);
  switch (i) {
    case 1:
      P(`tl.from('#s1-title', {y: 50, opacity: 0, duration: 0.6, ease: 'power3.out'}, at(0.2)); tl.from('#s1-sub', {y: 20, opacity: 0, duration: 0.4}, at(0.4));`);
      break;
    case 2:
      P(`tl.from('#s2-title', {y: 40, opacity: 0, duration: 0.5}, at(0.1)); tl.from('#s2-sub', {y: 20, opacity: 0, duration: 0.3}, at(0.3));`);
      break;
    case 3:
      P(`tl.from('#s3-title', {y: 30, opacity: 0, duration: 0.4}, at(0.2)); tl.from('#s3-sub', {y: 20, opacity: 0, duration: 0.2}, at(0.4));`);
      break;
    case 4:
      P(`tl.from('#s4-title', {y: 50, opacity: 0, duration: 0.6, ease: 'power3.out'}, at(0.2)); tl.from('#s4-sub', {y: 20, opacity: 0, duration: 0.4}, at(0.4));`);
      break;
    case 5:
      P(`tl.from('#s5-title', {y: 40, opacity: 0, duration: 0.5}, at(0.1)); tl.from('#s5-sub', {y: 20, opacity: 0, duration: 0.3}, at(0.3));`);
      break;
    case 6:
      P(`tl.from('#s6-title', {y: 30, opacity: 0, duration: 0.4}, at(0.2)); tl.from('#s6-sub', {y: 20, opacity: 0, duration: 0.2}, at(0.4));`);
      break;
    case 7:
      P(`tl.from('#s7-title', {y: 50, opacity: 0, duration: 0.6, ease: 'power3.out'}, at(0.2)); tl.from('#s7-sub', {y: 20, opacity: 0, duration: 0.4}, at(0.4));`);
      break;
    case 8:
      P(`tl.from('#s8-title', {y: 40, opacity: 0, duration: 0.5}, at(0.1)); tl.from('#s8-sub', {y: 20, opacity: 0, duration: 0.3}, at(0.3));`);
      break;

    case 9:
      P(`tl.from("#s9-eye",{y:-18,opacity:0,duration:.5,ease:"power2.out"},${at(0.2)});`);
      P(`tl.from("#s9-brand",{scale:.7,opacity:0,duration:.7,ease:"back.out(1.7)"},${at(0.5)});`);
      P(`tl.fromTo("#s9-rule",{scaleX:0},{scaleX:1,duration:.6,ease:"expo.out"},${at(1.1)});`);
      P(`tl.from(".cta-url",{y:20,opacity:0,duration:.55,ease:"power2.out"},${at(1.3)});`);
      P(`tl.fromTo("#s9-brand",{filter:"drop-shadow(0 0 0px rgba(var(--accent-rgb),0))"},{filter:"drop-shadow(0 0 26px rgba(var(--accent-rgb),.55))",duration:1.1,repeat:4,yoyo:true,ease:"sine.inOut"},${at(1.4)});`);
      P(`tl.from(["#s9-r1","#s9-r2"],{opacity:0,scale:.5,duration:.6,stagger:.12,ease:"back.out(2)"},${at(0.6)});`);
      break;
  }
  // caption
  P(`tl.fromTo("#cap-${i}",{opacity:0,y:14},{opacity:1,y:0,duration:.5,ease:"power2.out"},${at(0.35)});`);
  P(`tl.to("#cap-${i}",{opacity:0,duration:.4,ease:"power2.in"},${round(S[i-1].end - 0.55)});`);
  return L.join("\n      ");
}

// ---------- MONTAGEM ----------
const scenesHTML = S.map((s, idx) => `
    <section id="s${s.i}" class="scene clip" data-start="${s.start}" data-duration="${s.dur}" data-track-index="${s.i % 2 === 1 ? 1 : 3}">
      <div class="scene-inner" id="scene-inner-${s.i}">${BODIES[idx]()}</div>
    </section>`).join("");

const captionsHTML = S.map((s, idx) => `
    <div class="caption clip" id="cap-${s.i}" data-start="${s.start}" data-duration="${s.dur}" data-track-index="${s.i % 2 === 1 ? 2 : 4}">${CAPTIONS[idx]}</div>`).join("");

const audioHTML = S.map((s) => `
    <audio id="a${s.i}" data-start="${s.audioStart}" data-duration="${s.audioDur}" data-track-index="20" src="assets/audio/s${s.i}.wav"></audio>`).join("");

const animJS = S.map((s) => anim(s.i, s.start)).join("\n      ");

const html = `<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=${W}, height=${H}" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      ${FONT_CSS}
      :root{
        --bg:#000000; --bg2:#1D2D44; --bg3:#3E5C76;
        --fg:#F0EBD8; --muted:#748CAB; --accent:#DC143C; --accent2:#B8860B; --code:#2EC4B6;
        --accent-rgb: 220,20,60;
      }
      *{margin:0;padding:0;box-sizing:border-box}
      html,body{width:${W}px;height:${H}px;overflow:hidden;background:var(--bg);color:var(--fg);
        font-family:Inter,system-ui,sans-serif;-webkit-font-smoothing:antialiased}
      .mono{font-family:"JetBrains Mono",ui-monospace,monospace}
      #root{position:relative;width:${W}px;height:${H}px;overflow:hidden}

      /* ---- background persistente ---- */
      .bg-layer{position:absolute;inset:0;z-index:0;pointer-events:none}
      #glow{position:absolute;top:-260px;left:-180px;width:1100px;height:1100px;border-radius:50%;
        background:radial-gradient(circle,rgba(var(--accent-rgb),.20),rgba(var(--accent-rgb),0) 62%);filter:blur(8px)}
      #glow2{position:absolute;bottom:-360px;right:-240px;width:1200px;height:1200px;border-radius:50%;
        background:radial-gradient(circle,rgba(46,196,182,.10),rgba(46,196,182,0) 62%)}
      #grid{position:absolute;inset:-2px;opacity:.5;
        background-image:linear-gradient(rgba(116,140,171,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(116,140,171,.07) 1px,transparent 1px);
        background-size:64px 64px}
      .ghost{position:absolute;font-family:Sora,sans-serif;font-weight:800;color:rgba(var(--accent-rgb),.04);
        font-size:520px;line-height:.8;letter-spacing:-.03em;top:240px;left:-40px;white-space:nowrap;user-select:none}
      #grain{position:absolute;inset:0;opacity:.05;mix-blend-mode:overlay;
        background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
      #progress{position:absolute;left:0;bottom:0;height:6px;width:100%;transform:scaleX(0);transform-origin:left center;
        background:linear-gradient(90deg,var(--accent),var(--accent2));z-index:40;box-shadow:0 0 18px rgba(var(--accent-rgb),.5)}

      /* ---- cena base ---- */
      .scene{position:absolute;inset:0;z-index:10;display:flex;flex-direction:column;justify-content:center;
        padding:120px 150px 150px}
      .scene-inner{position:relative;width:100%;height:100%;display:flex;flex-direction:column;justify-content:center}
      .kicker{font-family:"JetBrains Mono",monospace;font-size:22px;letter-spacing:.28em;color:var(--accent);
        text-transform:uppercase;margin-bottom:26px;font-weight:600}
      .kicker.center{text-align:center}
      .h2{font-family:Sora,sans-serif;font-weight:800;font-size:92px;line-height:1.02;letter-spacing:-.02em}
      .h2.center{text-align:center}
      .lead{font-size:34px;color:var(--muted);margin-top:30px}.lead b{color:var(--fg)}
      .accent{color:var(--accent)}.accent2{color:var(--accent2)}.dim{color:var(--muted)}

      /* cena 1 */
      .eyebrow{display:inline-flex;align-items:center;gap:14px;font-family:"JetBrains Mono",monospace;
        font-size:26px;letter-spacing:.3em;color:var(--muted);font-weight:600}
      .eyebrow .dot{width:14px;height:14px;border-radius:50%;background:var(--accent);box-shadow:0 0 16px var(--accent)}
      .title{font-family:Sora,sans-serif;font-weight:800;font-size:172px;line-height:.95;letter-spacing:-.03em;margin:24px 0}
      .title .word{display:block}
      .rule{height:7px;width:520px;background:linear-gradient(90deg,var(--accent),var(--accent2));border-radius:6px;margin:10px 0 30px}
      .rule.center{margin:34px auto}
      .subhead{font-size:40px;color:var(--muted)}
      .cursor{display:inline-block;width:18px;height:38px;background:var(--accent);margin-left:10px;vertical-align:-4px;border-radius:2px}
      .reg{position:absolute;width:48px;height:48px;border:3px solid var(--bg3)}
      .reg.tl{top:0;left:0;border-right:none;border-bottom:none}
      .reg.br{bottom:0;right:0;border-left:none;border-top:none}

      /* layout 2 colunas */
      .grid2{display:grid;grid-template-columns:1fr 1fr;gap:90px;align-items:center;width:100%}
      .grid2 .right{display:flex;flex-direction:column}

      /* cena 2 folder */
      .folder{position:relative;width:520px;height:360px;margin:0 auto}
      .folder-tab{position:absolute;top:6px;left:0;width:210px;height:54px;background:var(--accent2);border-radius:16px 16px 0 0}
      .folder-body{position:absolute;top:46px;left:0;width:520px;height:300px;background:linear-gradient(160deg,#24395a,var(--bg2));
        border:2px solid var(--bg3);border-radius:8px 22px 22px 22px;display:flex;align-items:flex-end;padding:26px;font-size:30px;color:var(--muted)}
      .file-card{position:absolute;top:120px;left:120px;display:flex;align-items:center;gap:16px;background:#0a1b2e;
        border:2px solid var(--accent);border-radius:14px;padding:24px 34px;font-size:34px;color:var(--fg);
        box-shadow:0 24px 60px rgba(0,0,0,.5)}
      .file-dot{width:16px;height:16px;border-radius:50%;background:var(--accent);box-shadow:0 0 14px var(--accent)}
      .chips{display:flex;gap:18px;margin-top:38px;flex-wrap:wrap}
      .chip{background:rgba(116,140,171,.12);border:2px solid var(--bg3);border-radius:999px;padding:16px 30px;
        font-size:28px;color:var(--fg);font-weight:600}
      .kicker:not(.center){display:inline-block}

      /* cena 3 código */
      .code{width:1360px;margin:8px auto 0;background:#0a1626;border:2px solid var(--bg3);border-radius:18px;overflow:hidden;
        box-shadow:0 30px 80px rgba(0,0,0,.5)}
      .code-bar{display:flex;align-items:center;gap:12px;padding:20px 28px;background:#0c1a2c;border-bottom:2px solid var(--bg3)}
      .code-bar i{width:16px;height:16px;border-radius:50%;background:#2a3f5c}
      .code-bar .dim{margin-left:18px;font-size:24px}
      .code pre{padding:34px 40px;font-size:33px;line-height:1.6;color:var(--fg);white-space:pre}
      .code .key{color:var(--accent)}.code .val{color:var(--code)}.code .punc{color:var(--muted)}
      .code .ln{display:block;position:relative}
      .code .hl{position:relative;color:var(--fg)}
      .marker{position:absolute;left:-6px;right:-6px;top:1px;bottom:1px;background:rgba(var(--accent-rgb),.30);
        border-radius:6px;transform:scaleX(0);transform-origin:left center;z-index:-1}
      .tagrow{display:flex;align-items:center;gap:26px;justify-content:center;margin-top:46px;flex-wrap:wrap}
      .tag{background:rgba(116,140,171,.12);border:2px solid var(--bg3);border-radius:12px;padding:16px 28px;font-size:28px}
      .tag b{color:var(--accent)}.tag.accent2{border-color:var(--accent)}.tag.accent2 b{color:var(--accent2)}
      .arrow-note{font-family:"JetBrains Mono",monospace;color:var(--accent);font-size:26px}

      /* cena 4 camadas */
      .layers{display:flex;flex-direction:column;gap:24px;width:1180px;margin:0 auto}
      .layer{--lit:0;display:flex;align-items:center;gap:30px;background:linear-gradient(90deg,rgba(var(--accent-rgb),calc(.06*var(--lit))),var(--bg2));
        border:2px solid var(--bg3);border-radius:18px;padding:30px 40px}
      .lnum{width:64px;height:64px;flex:none;border-radius:50%;background:var(--bg2);border:2px solid var(--bg3);
        display:flex;align-items:center;justify-content:center;font-family:Sora;font-weight:800;font-size:32px;color:var(--accent)}
      .ltxt{display:flex;flex-direction:column;flex:1}
      .ltxt b{font-size:40px;font-family:Sora;font-weight:700}
      .lsub{font-size:26px;color:var(--muted);margin-top:4px}
      .lbadge{font-family:"JetBrains Mono",monospace;font-size:22px;color:var(--bg);background:var(--accent);
        padding:8px 18px;border-radius:999px;font-weight:700}
      .layer#s4-L2 .lbadge{background:var(--accent2)}
      .layer#s4-L3 .lbadge{background:var(--code)}
      .meter{display:flex;align-items:center;gap:24px;width:1180px;margin:38px auto 0}
      .meter-label{font-size:24px;color:var(--muted)}
      .meter-bar{flex:1;height:22px;background:var(--bg2);border:2px solid var(--bg3);border-radius:999px;overflow:hidden}
      .meter-fill{height:100%;width:100%;transform:scaleX(0);transform-origin:left center;
        background:linear-gradient(90deg,var(--code),var(--accent));border-radius:999px}
      .meter-val{font-size:26px;color:var(--code);font-weight:700}

      /* cena 5 paths */
      .paths{display:grid;grid-template-columns:1fr 1fr;gap:40px;width:1180px;margin:0 auto}
      .pathcard{background:linear-gradient(160deg,#22364f,var(--bg2));border:2px solid var(--bg3);border-radius:20px;padding:44px}
      .ptag{display:inline-block;font-size:22px;letter-spacing:.2em;color:var(--bg);background:var(--muted);
        padding:8px 18px;border-radius:8px;font-weight:700;margin-bottom:24px}
      .ptag.accentbg{background:var(--accent)}
      .ppath{font-size:46px;color:var(--fg);font-weight:600}
      .pdesc{font-size:28px;color:var(--muted);margin-top:18px}
      .term{width:1180px;margin:40px auto 0;background:#0a1626;border:2px solid var(--bg3);border-radius:14px;
        padding:30px 38px;font-size:38px;display:flex;align-items:center}
      .term .prompt{color:var(--code);margin-right:18px}
      .term .cmd{color:var(--fg)}

      /* cena 6 bullets + tree */
      .bullets{list-style:none;margin:34px 0 0;display:flex;flex-direction:column;gap:22px}
      .bullets li{display:flex;align-items:center;gap:20px;font-size:34px;color:var(--fg)}
      .bdot{width:16px;height:16px;flex:none;border-radius:4px;background:var(--accent);box-shadow:0 0 12px var(--accent);transform:rotate(45deg)}
      .tree{background:#0a1626;border:2px solid var(--bg3);border-radius:18px;padding:40px 44px;box-shadow:0 30px 80px rgba(0,0,0,.5)}
      .trow{font-size:38px;line-height:1.9;color:var(--fg);border-radius:8px;padding:0 12px}
      .trow.root{color:var(--accent);font-weight:700}
      .runtag{font-family:"JetBrains Mono";font-size:22px;color:var(--bg);background:var(--code);padding:4px 14px;border-radius:8px;margin-left:14px;font-weight:700}

      /* cena 7 meta */
      .meta-top{text-align:center;font-size:34px;color:var(--muted)}
      .badge{position:relative;width:560px;height:130px;margin:48px auto;display:flex;align-items:center;justify-content:center;
        background:linear-gradient(120deg,#22364f,var(--bg2));border:2px solid var(--accent);border-radius:22px;
        box-shadow:0 24px 70px rgba(0,0,0,.5)}
      .badge-name{font-family:Sora;font-weight:800;font-size:60px;letter-spacing:-.01em;
        background:linear-gradient(90deg,var(--accent),var(--accent2));-webkit-background-clip:text;background-clip:text;color:transparent}
      .badge-halo{position:absolute;inset:-2px;border-radius:22px;border:2px solid var(--accent);opacity:.6}
      .flow{display:flex;align-items:center;justify-content:center;gap:34px;font-size:52px;color:var(--fg)}
      .flow .farr{color:var(--accent)}
      .flow .big{font-size:72px}

      /* cena 8 fecho */
      .closer-sub{text-align:center;font-size:34px;color:var(--muted);margin-bottom:20px}
      .closer{text-align:center;font-family:Sora;font-weight:800;font-size:128px;line-height:1.02;letter-spacing:-.02em}
      .sig{text-align:center;font-size:30px;color:var(--accent);letter-spacing:.3em;text-transform:uppercase;margin-top:20px}

      /* cena 9 CTA (INEMA.CLUB) */
      .cta-eyebrow{text-align:center;font-family:"JetBrains Mono",monospace;font-size:26px;letter-spacing:.36em;
        color:var(--muted);text-transform:uppercase;margin-bottom:30px}
      .cta-brand{text-align:center;font-family:Sora;font-weight:800;font-size:150px;line-height:.95;letter-spacing:-.02em}
      .cta-brand .b1{color:var(--fg)}.cta-brand .b2{color:var(--accent)}.cta-brand .bdotsep{color:var(--accent)}
      .cta-url{display:flex;align-items:center;justify-content:center;gap:16px;font-size:46px;color:var(--muted);margin-top:32px}
      .cta-globe{font-size:38px;filter:grayscale(.2)}

      /* caption */
      .caption{position:absolute;left:50%;transform:translateX(-50%);bottom:64px;z-index:30;
        max-width:1500px;text-align:center;font-size:36px;font-weight:600;color:var(--fg);
        background:rgba(10,18,30,.72);border:1px solid var(--bg3);border-radius:14px;padding:18px 40px;
        backdrop-filter:blur(6px);text-shadow:0 2px 10px rgba(0,0,0,.6)}

      /* =================== OVERRIDES 9:16 (Shorts) =================== */
      body.v .scene{padding:170px 70px 240px}
      body.v .grid2{grid-template-columns:1fr;gap:54px}
      body.v .kicker{margin-bottom:20px;font-size:20px}
      body.v .h2{font-size:74px}
      body.v .lead{font-size:30px;margin-top:24px}
      /* cena 1 */
      body.v .eyebrow{font-size:22px}
      body.v .title{font-size:118px;margin:20px 0}
      body.v .rule{width:360px;margin-bottom:24px}
      body.v .subhead{font-size:34px}
      /* cena 2 */
      body.v .folder{width:440px;height:300px}
      body.v .folder-body{width:440px;height:254px}
      body.v .file-card{font-size:30px;top:110px;left:96px}
      body.v .chips{margin-top:30px;gap:14px}
      body.v .chip{font-size:26px;padding:14px 24px}
      /* cena 3 */
      body.v .code{width:940px}
      body.v .code pre{font-size:23px;padding:26px 30px;line-height:1.6}
      body.v .code-bar .dim{font-size:20px}
      body.v .tagrow{gap:16px;margin-top:36px}
      body.v .tag{font-size:23px;padding:12px 20px}
      body.v .arrow-note{font-size:22px}
      /* cena 4 */
      body.v .layers{width:940px;gap:18px}
      body.v .layer{padding:22px 26px;gap:22px}
      body.v .lnum{width:54px;height:54px;font-size:28px}
      body.v .ltxt b{font-size:34px}
      body.v .lsub{font-size:22px}
      body.v .lbadge{font-size:18px;padding:6px 14px}
      body.v .meter{width:940px;margin-top:30px}
      /* cena 5 */
      body.v .paths{grid-template-columns:1fr;gap:26px;width:940px}
      body.v .pathcard{padding:36px}
      body.v .ppath{font-size:42px}
      body.v .pdesc{font-size:26px}
      body.v .term{width:940px;font-size:31px;margin-top:34px}
      /* cena 6 */
      body.v .bullets{margin-top:28px;gap:18px}
      body.v .bullets li{font-size:30px}
      body.v .tree{padding:32px 34px}
      body.v .trow{font-size:30px;line-height:1.85}
      /* cena 7 */
      body.v .meta-top{font-size:30px}
      body.v .h2.center{font-size:78px}
      body.v .badge{width:480px;height:118px;margin:42px auto}
      body.v .badge-name{font-size:54px}
      body.v .flow{font-size:44px;gap:24px}
      body.v .flow .big{font-size:60px}
      /* cena 8 */
      body.v .closer-sub{font-size:30px}
      body.v .closer{font-size:104px}
      body.v .sig{font-size:28px}
      /* cena 9 */
      body.v .cta-brand{font-size:116px}
      body.v .cta-url{font-size:42px}
      /* caption no vertical: sobe pra não cortar */
      body.v .caption{bottom:150px;max-width:940px;font-size:33px;padding:16px 32px}
      /* glows reposicionados pro frame alto */
      body.v #glow{top:-200px;left:-160px;width:900px;height:900px}
      body.v #glow2{bottom:-300px;right:-200px;width:1000px;height:1000px}
      body.v .ghost{font-size:380px;top:520px}
      /* ---- background de mídia real (foto/vídeo B-roll) ---- */
      #bg-media{position:absolute;inset:0;z-index:0;pointer-events:none;overflow:hidden}
      #bg-media::after{content:'';position:absolute;inset:0;background:rgba(0,0,0,0.30)}
      
      /* ---- backgrounds por cena --- */
      .scene-bg{
        position:absolute;inset:0;z-index:1;pointer-events:none;
        background-size:cover;background-position:center center;
        background-repeat:no-repeat;
      }
      .scene-bg::after{
        content:'';position:absolute;inset:0;
        background:rgba(0,0,0,0.50);z-index:1;
      }
      .scene-bg video,.scene-bg img{
        position:absolute;inset:0;width:100%;height:100%;
        object-fit:cover;z-index:0;
      }
    </style>
  </head>
  <body class="${VERT ? "v" : ""}" style="">
    <div id="root" data-composition-id="main" data-start="0" data-duration="${TOTAL}" data-width="${W}" data-height="${H}">
      <div class="bg-layer" data-layout-ignore>
        <div id="bg-media">
      <div class="scene-bg" id="scene-bg-1"><video autoplay muted loop playsinline style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0;"><source src="assets/bg_scenes/bg_s1.mp4" type="video/mp4"></video><div style="position:absolute;inset:0;background:rgba(0,0,0,0.50);z-index:1;"></div></div>
      <div class="scene-bg" id="scene-bg-2"><video autoplay muted loop playsinline style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0;"><source src="assets/bg_scenes/bg_s2.mp4" type="video/mp4"></video><div style="position:absolute;inset:0;background:rgba(0,0,0,0.50);z-index:1;"></div></div>
      <div class="scene-bg" id="scene-bg-3"><video autoplay muted loop playsinline style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0;"><source src="assets/bg_scenes/bg_s3.mp4" type="video/mp4"></video><div style="position:absolute;inset:0;background:rgba(0,0,0,0.50);z-index:1;"></div></div>
      <div class="scene-bg" id="scene-bg-4"><video autoplay muted loop playsinline style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0;"><source src="assets/bg_scenes/bg_s4.mp4" type="video/mp4"></video><div style="position:absolute;inset:0;background:rgba(0,0,0,0.50);z-index:1;"></div></div>
      <div class="scene-bg" id="scene-bg-5"><video autoplay muted loop playsinline style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0;"><source src="assets/bg_scenes/bg_s5.mp4" type="video/mp4"></video><div style="position:absolute;inset:0;background:rgba(0,0,0,0.50);z-index:1;"></div></div>
      <div class="scene-bg" id="scene-bg-6"><video autoplay muted loop playsinline style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0;"><source src="assets/bg_scenes/bg_s6.mp4" type="video/mp4"></video><div style="position:absolute;inset:0;background:rgba(0,0,0,0.50);z-index:1;"></div></div>
      <div class="scene-bg" id="scene-bg-7"><video autoplay muted loop playsinline style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0;"><source src="assets/bg_scenes/bg_s7.mp4" type="video/mp4"></video><div style="position:absolute;inset:0;background:rgba(0,0,0,0.50);z-index:1;"></div></div>
      <div class="scene-bg" id="scene-bg-8"><video autoplay muted loop playsinline style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0;"><source src="assets/bg_scenes/bg_s8.mp4" type="video/mp4"></video><div style="position:absolute;inset:0;background:rgba(0,0,0,0.50);z-index:1;"></div></div></div>
        <div id="glow"></div><div id="glow2"></div><div id="grid"></div>
        <div class="ghost" id="ghost" data-layout-ignore>JESUS</div><div id="grain"></div>
      </div>
${scenesHTML}
${captionsHTML}
      <div id="progress"></div>
${audioHTML}
<audio id="soundtrack" src="assets/audio/soundtrack.mp3" loop style="display:none"></audio>
      <script>
        window.__timelines = window.__timelines || {};
        const tl = gsap.timeline({ paused: true });
        const TOTAL = ${TOTAL};
        // ambiente (volume e luz)
        const soundtrackEl = document.getElementById("soundtrack");
        if(soundtrackEl) { soundtrackEl.volume = 0.08; }
        tl.to("#glow",{scale:1.22,opacity:.55,duration:4.5,yoyo:true,repeat:Math.ceil(TOTAL/4.5)+1,ease:"sine.inOut"},0);
        tl.to("#glow2",{scale:1.18,duration:6,yoyo:true,repeat:Math.ceil(TOTAL/6)+1,ease:"sine.inOut"},0);
        tl.to("#ghost",{x:120,duration:TOTAL,ease:"none"},0);
        tl.to("#grid",{backgroundPositionX:"+=128",backgroundPositionY:"+=128",duration:18,repeat:Math.ceil(TOTAL/18)+1,ease:"none"},0);
        tl.fromTo("#progress",{scaleX:0},{scaleX:1,duration:TOTAL,ease:"none"},0);
        // cenas
      ${animJS}
        // sentinela: estende a timeline até o fim da composição
        tl.set({}, {}, TOTAL);
        window.__timelines["main"] = tl;
        
        // ---- Backgrounds por cena via GSAP ----
        gsap.set('#scene-bg-1', {opacity: 0});
        gsap.set('#scene-bg-2', {opacity: 0});
        gsap.set('#scene-bg-3', {opacity: 0});
        gsap.set('#scene-bg-4', {opacity: 0});
        gsap.set('#scene-bg-5', {opacity: 0});
        gsap.set('#scene-bg-6', {opacity: 0});
        gsap.set('#scene-bg-7', {opacity: 0});
        gsap.set('#scene-bg-8', {opacity: 0});
        gsap.set('#scene-bg-1', {opacity: 1});
        // bg cena 1 -> 2
        // bg cena 2 -> 3
        // bg cena 3 -> 4
        // bg cena 4 -> 5
        // bg cena 5 -> 6
        // bg cena 6 -> 7
        // bg cena 7 -> 8
        // Liga IntersectionObserver para troca suave
        (function() {
          const bgIds = {1: 'scene-bg-1', 2: 'scene-bg-2', 3: 'scene-bg-3', 4: 'scene-bg-4', 5: 'scene-bg-5', 6: 'scene-bg-6', 7: 'scene-bg-7', 8: 'scene-bg-8'};
          function activateBg(n) {
            Object.values(bgIds).forEach(id => {
              const el = document.getElementById(id);
              if (el) el.style.opacity = '0';
            });
            const t = document.getElementById(bgIds[n]);
            if (t) t.style.opacity = '1';
          }
          activateBg(1);
          const obs = new IntersectionObserver(function(entries) {
            entries.forEach(function(e) {
              if (e.isIntersecting) {
                const si = parseInt(e.target.id.replace('s',''));
                if (bgIds[si] !== undefined) activateBg(si);
              }
            });
          }, {threshold: 0.3, root: document.getElementById('root')});
          document.querySelectorAll('.scene').forEach(s => obs.observe(s));
        })();

      </script>
    </div>
  </body>
</html>
`;

writeFileSync(new URL("./" + OUT, import.meta.url), html);
console.log(`${OUT} gerado · ${W}x${H} · TOTAL = ${TOTAL}s · ${S.length} cenas`);
S.forEach(s => console.log(`  s${s.i}: start=${s.start} dur=${s.dur} audio@${s.audioStart} (${s.audioDur}s)`));
