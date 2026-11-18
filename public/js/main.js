/* ═══════════════════════════════════════════════════════
   LUNA — main.js  |  Interatividade do frontend
   ═══════════════════════════════════════════════════════ */

/* ── Tabs (login + matéria) ─────────────────────────────── */
document.addEventListener('DOMContentLoaded', function () {

  // Tabs genéricas (data-tab)
  document.querySelectorAll('.tab-btn[data-tab]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var targetId = 'tab-' + btn.dataset.tab;

      // Pega o container de tabs pai
      var container = btn.closest('.login-tabs, .tabs');
      if (!container) return;

      // Desativa todos os botões do mesmo container
      container.querySelectorAll('.tab-btn').forEach(function (b) {
        b.classList.remove('active');
      });
      btn.classList.add('active');

      // Esconde todos os panels irmãos
      var panels = document.querySelectorAll('.tab-panel');
      panels.forEach(function (p) { p.style.display = 'none'; p.classList.remove('active'); });

      // Mostra o panel alvo
      var target = document.getElementById(targetId);
      if (target) { target.style.display = ''; target.classList.add('active'); }
    });
  });

  // Scroll para o fim do chat ao carregar
  scrollChatBottom();
});

/* ── Chat principal ─────────────────────────────────────── */
function scrollChatBottom() {
  var msgs = document.getElementById('chat-msgs');
  if (msgs) msgs.scrollTop = msgs.scrollHeight;
}

function tokenCSRF() {
  var meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.content : '';
}

function criarBolha(tipo, texto) {
  var div = document.createElement('div');
  div.className = 'msg-bubble ' + tipo;

  if (tipo === 'luna') {
    var avatar = document.createElement('div');
    avatar.className = 'luna-avatar-sm';
    avatar.textContent = 'L';
    div.appendChild(avatar);
  }

  var content = document.createElement('div');
  content.className = 'msg-content';

  var text = document.createElement('div');
  text.className = 'msg-text';
  text.innerHTML = escaparHTML(texto).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  content.appendChild(text);
  div.appendChild(content);
  return div;
}

function escaparHTML(texto) {
  return texto.replace(/[&<>"']/g, function (caractere) {
    return {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    }[caractere];
  }).replace(/\n/g, '<br>');
}

function mostrarErroChat(mensagem) {
  var msgs = document.getElementById('chat-msgs');
  if (!msgs) return;
  var aviso = document.createElement('div');
  aviso.className = 'msg-bubble luna';
  var conteudo = document.createElement('div');
  conteudo.className = 'msg-content';
  var texto = document.createElement('div');
  texto.className = 'msg-text';
  texto.textContent = mensagem;
  conteudo.appendChild(texto);
  aviso.appendChild(conteudo);
  msgs.appendChild(aviso);
  scrollChatBottom();
}

function mostrarTyping() {
  var msgs = document.getElementById('chat-msgs');
  if (!msgs) return null;
  var bubble = document.createElement('div');
  bubble.className = 'msg-bubble luna typing-bubble';
  bubble.id = 'typing-indicator';

  var avatar = document.createElement('div');
  avatar.className = 'luna-avatar-sm';
  avatar.textContent = 'L';

  var content = document.createElement('div');
  content.className = 'msg-content';
  var text = document.createElement('div');
  text.className = 'msg-text';
  text.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
  content.appendChild(text);
  bubble.appendChild(avatar);
  bubble.appendChild(content);
  msgs.appendChild(bubble);
  scrollChatBottom();
  return bubble;
}

function removerTyping() {
  var el = document.getElementById('typing-indicator');
  if (el) el.remove();
}

function enviarMensagem() {
  var input = document.getElementById('chat-input');
  if (!input) return;
  var texto = input.value.trim();
  if (!texto) return;

  var msgs = document.getElementById('chat-msgs');
  msgs.appendChild(criarBolha('aluno', texto));
  input.value = '';
  scrollChatBottom();

  var typing = mostrarTyping();

  fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': tokenCSRF() },
    body: JSON.stringify({ mensagem: texto })
  })
  .then(function (r) {
    return r.json().then(function (data) {
      if (!r.ok) throw new Error(data.erro || 'Não foi possível obter uma resposta.');
      return data;
    });
  })
  .then(function (data) {
    removerTyping();
    var resposta = data.resposta || 'Ops, algo deu errado. Tenta de novo!';
    // Delay leve para parecer mais natural
    setTimeout(function () {
      msgs.appendChild(criarBolha('luna', resposta));
      scrollChatBottom();
    }, 300);
  })
  .catch(function (erro) {
    removerTyping();
    mostrarErroChat(erro.message || 'Desculpa, tive um problema de conexão. Tenta novamente! 😅');
  });
}

function usarSugestao(btn) {
  var input = document.getElementById('chat-input');
  if (input) {
    input.value = btn.textContent;
    enviarMensagem();
  }
}

function limparChat() {
  if (!confirm('Limpar o histórico da conversa?')) return;
  fetch('/api/limpar_chat', {
    method: 'POST',
    headers: { 'X-CSRFToken': tokenCSRF() }
  })
  .then(function (response) {
    if (!response.ok) throw new Error('Não foi possível limpar o histórico.');
    return response.json();
  })
  .then(function () {
    var msgs = document.getElementById('chat-msgs');
    if (msgs) msgs.innerHTML = '';
  })
  .catch(function (erro) {
    mostrarErroChat(erro.message);
  });
}

/* ── Mini chat (página de matéria) ─────────────────────── */
function enviarMiniChat() {
  var input = document.getElementById('mini-input');
  if (!input) return;
  var texto = input.value.trim();
  if (!texto) return;

  var msgs = document.getElementById('mini-msgs');
  msgs.appendChild(criarBolhaMini('aluno', texto));
  input.value = '';
  msgs.scrollTop = msgs.scrollHeight;

  // Typing indicator mini
  var typing = document.createElement('div');
  typing.id = 'mini-typing';
  typing.className = 'msg-bubble luna typing-bubble';
  typing.innerHTML = '<div class="luna-avatar-sm">L</div><div class="msg-content"><div class="msg-text"><div class="typing-dots"><span></span><span></span><span></span></div></div></div>';
  msgs.appendChild(typing);
  msgs.scrollTop = msgs.scrollHeight;

  var materiaCtx = (typeof MATERIA_ATUAL !== 'undefined') ? MATERIA_ATUAL : null;

  fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': tokenCSRF() },
    body: JSON.stringify({ mensagem: texto, materia: materiaCtx })
  })
  .then(function (r) {
    return r.json().then(function (data) {
      if (!r.ok) throw new Error(data.erro || 'Não foi possível obter uma resposta.');
      return data;
    });
  })
  .then(function (data) {
    var t = document.getElementById('mini-typing');
    if (t) t.remove();
    setTimeout(function () {
      msgs.appendChild(criarBolhaMini('luna', data.resposta || 'Ops!'));
      msgs.scrollTop = msgs.scrollHeight;
    }, 250);
  })
  .catch(function (erro) {
    var t = document.getElementById('mini-typing');
    if (t) t.remove();
    msgs.appendChild(criarBolhaMini('luna', erro.message || 'Problema de conexão. Tenta de novo!'));
    msgs.scrollTop = msgs.scrollHeight;
  });
}

function criarBolhaMini(tipo, texto) {
  var div = document.createElement('div');
  div.className = 'msg-bubble ' + tipo;
  if (tipo === 'luna') {
    var av = document.createElement('div');
    av.className = 'luna-avatar-sm';
    av.textContent = 'L';
    div.appendChild(av);
  }
  var content = document.createElement('div');
  content.className = 'msg-content';
  var text = document.createElement('div');
  text.className = 'msg-text';
  text.innerHTML = escaparHTML(texto).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  content.appendChild(text);
  div.appendChild(content);
  return div;
}

/* ── Exercícios: revelar resposta ───────────────────────── */
function revelarResposta(btn) {
  var card = btn.closest('.exercicio-card');
  if (!card) return;
  var resp = card.querySelector('.exercicio-resposta');
  if (!resp) return;
  if (resp.style.display === 'none' || resp.style.display === '') {
    resp.style.display = 'block';
    btn.textContent = 'Esconder resposta';
    btn.style.borderColor = 'var(--gray-6)';
    btn.style.color = 'var(--white)';
  } else {
    resp.style.display = 'none';
    btn.textContent = 'Ver resposta';
    btn.style.borderColor = '';
    btn.style.color = '';
  }
}
