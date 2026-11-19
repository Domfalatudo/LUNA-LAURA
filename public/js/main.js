document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.tab-btn[data-tab]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var container = btn.closest('.login-tabs, .tabs');
      if (!container) return;
      container.querySelectorAll('.tab-btn').forEach(function (item) {
        item.classList.remove('active');
      });
      btn.classList.add('active');
      var panels = document.querySelectorAll('.tab-panel');
      panels.forEach(function (panel) {
        panel.style.display = 'none';
        panel.classList.remove('active');
      });
      var target = document.getElementById('tab-' + btn.dataset.tab);
      if (target) {
        target.style.display = '';
        target.classList.add('active');
      }
    });
  });

  renderAllMarkdown();
  iniciarChat();
  iniciarQuiz();
  iniciarFlashcards();
  scrollChatBottom();
});

function tokenCSRF() {
  var meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.content : '';
}

function escaparHTML(texto) {
  return String(texto).replace(/[&<>"']/g, function (caractere) {
    return {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    }[caractere];
  });
}

function markdownSeguro(texto) {
  if (window.marked && window.DOMPurify) {
    window.marked.setOptions({ breaks: true, gfm: true });
    return window.DOMPurify.sanitize(window.marked.parse(String(texto)));
  }
  return escaparHTML(texto).replace(/\r?\n/g, '<br>');
}

function atualizarMatematica(elemento) {
  if (!window.MathJax || !window.MathJax.typesetPromise) return;
  var pronto = window.MathJax.startup && window.MathJax.startup.promise;
  Promise.resolve(pronto).then(function () {
    return window.MathJax.typesetPromise([elemento]);
  }).catch(function () {});
}

function renderMarkdownElement(elemento) {
  if (!elemento || elemento.dataset.rendered === 'true') return;
  var source = elemento.textContent;
  elemento.innerHTML = markdownSeguro(source);
  elemento.dataset.rendered = 'true';
  atualizarMatematica(elemento);
}

function renderAllMarkdown() {
  document.querySelectorAll('[data-markdown]').forEach(renderMarkdownElement);
}

function renderMessage(tipo, texto) {
  var bubble = document.createElement('div');
  bubble.className = 'msg-bubble ' + tipo;
  if (tipo === 'luna') {
    var avatar = document.createElement('div');
    avatar.className = 'luna-avatar-sm';
    avatar.textContent = 'L';
    bubble.appendChild(avatar);
  }
  var content = document.createElement('div');
  content.className = 'msg-content';
  var message = document.createElement('div');
  message.className = 'msg-text';
  message.innerHTML = markdownSeguro(texto);
  content.appendChild(message);
  bubble.appendChild(content);
  atualizarMatematica(message);
  return bubble;
}

function scrollChatBottom() {
  var messages = document.getElementById('chat-msgs');
  if (messages) messages.scrollTop = messages.scrollHeight;
}

function mostrarErroChat(mensagem) {
  var messages = document.getElementById('chat-msgs');
  if (!messages) return;
  var bubble = document.createElement('div');
  bubble.className = 'chat-error-note';
  bubble.textContent = mensagem;
  messages.appendChild(bubble);
  scrollChatBottom();
}

function mostrarTyping() {
  var messages = document.getElementById('chat-msgs');
  if (!messages) return;
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
  messages.appendChild(bubble);
  scrollChatBottom();
}

function removerTyping() {
  var indicator = document.getElementById('typing-indicator');
  if (indicator) indicator.remove();
}

function iniciarChat() {
  var input = document.getElementById('chat-input');
  if (input) {
    input.addEventListener('keydown', function (event) {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        enviarMensagem();
      }
    });
    input.addEventListener('input', function () {
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 150) + 'px';
    });
  }
  var newButton = document.getElementById('new-conversation');
  if (newButton) {
    newButton.addEventListener('click', function () {
      fetch('/api/chat/conversas', {
        method: 'POST',
        headers: { 'X-CSRFToken': tokenCSRF() }
      }).then(function (response) {
        if (!response.ok) throw new Error('Não foi possível iniciar outra conversa.');
        return response.json();
      }).then(function (data) {
        window.location.href = '/chat?conversa=' + encodeURIComponent(data.id);
      }).catch(function (error) {
        mostrarErroChat(error.message);
      });
    });
  }
  document.querySelectorAll('[data-delete-conversation]').forEach(function (button) {
    button.addEventListener('click', function () {
      if (!confirm('Excluir esta conversa permanentemente?')) return;
      fetch('/api/chat/conversas/' + encodeURIComponent(button.dataset.deleteConversation), {
        method: 'DELETE',
        headers: { 'X-CSRFToken': tokenCSRF() }
      }).then(function (response) {
        return response.json().then(function (data) {
          if (!response.ok) throw new Error(data.erro || 'Não foi possível excluir a conversa.');
          return data;
        });
      }).then(function (data) {
        window.location.href = '/chat?conversa=' + encodeURIComponent(data.id);
      }).catch(function (error) {
        mostrarErroChat(error.message);
      });
    });
  });
}

function enviarMensagem() {
  var input = document.getElementById('chat-input');
  var button = document.getElementById('chat-send');
  var messages = document.getElementById('chat-msgs');
  if (!input || !messages) return;
  var texto = input.value.trim();
  if (!texto || (button && button.disabled)) return;
  messages.appendChild(renderMessage('aluno', texto));
  input.value = '';
  input.style.height = 'auto';
  if (button) button.disabled = true;
  mostrarTyping();

  fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': tokenCSRF() },
    body: JSON.stringify({ mensagem: texto })
  }).then(function (response) {
    return response.json().then(function (data) {
      if (!response.ok) throw new Error(data.erro || 'Não foi possível obter uma resposta.');
      return data;
    });
  }).then(function (data) {
    removerTyping();
    messages.appendChild(renderMessage('luna', data.resposta || 'Não recebi uma resposta.'));
    scrollChatBottom();
  }).catch(function (error) {
    removerTyping();
    mostrarErroChat(error.message || 'Problema de conexão. Tente novamente.');
  }).finally(function () {
    if (button) button.disabled = false;
    input.focus();
  });
}

function usarSugestao(button) {
  var input = document.getElementById('chat-input');
  if (input) {
    input.value = button.textContent;
    enviarMensagem();
  }
}

function limparChat() {
  if (!confirm('Apagar as mensagens desta conversa?')) return;
  fetch('/api/limpar_chat', {
    method: 'POST',
    headers: { 'X-CSRFToken': tokenCSRF() }
  }).then(function (response) {
    if (!response.ok) throw new Error('Não foi possível limpar as mensagens.');
    window.location.reload();
  }).catch(function (error) {
    mostrarErroChat(error.message);
  });
}

function criarBolhaMini(tipo, texto) {
  var bubble = renderMessage(tipo, texto);
  bubble.classList.add('mini-message');
  return bubble;
}

function enviarMiniChat() {
  var input = document.getElementById('mini-input');
  var messages = document.getElementById('mini-msgs');
  if (!input || !messages) return;
  var texto = input.value.trim();
  if (!texto) return;
  messages.appendChild(criarBolhaMini('aluno', texto));
  input.value = '';
  var context = typeof MATERIA_ATUAL !== 'undefined' ? MATERIA_ATUAL : null;
  fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': tokenCSRF() },
    body: JSON.stringify({ mensagem: texto, materia: context })
  }).then(function (response) {
    return response.json().then(function (data) {
      if (!response.ok) throw new Error(data.erro || 'Não foi possível obter uma resposta.');
      return data;
    });
  }).then(function (data) {
    messages.appendChild(criarBolhaMini('luna', data.resposta));
    messages.scrollTop = messages.scrollHeight;
  }).catch(function (error) {
    messages.appendChild(criarBolhaMini('luna', error.message));
    messages.scrollTop = messages.scrollHeight;
  });
}

function iniciarQuiz() {
  var button = document.getElementById('grade-quiz');
  if (!button) return;
  button.addEventListener('click', function () {
    var questions = document.querySelectorAll('.quiz-question');
    var correctCount = 0;
    questions.forEach(function (question) {
      var selected = question.querySelector('input[type="radio"]:checked');
      var answer = Number(question.dataset.correct);
      var explanation = question.querySelector('.quiz-explanation');
      question.querySelectorAll('.quiz-option').forEach(function (option) {
        option.classList.remove('is-correct', 'is-wrong');
      });
      if (selected) {
        var option = selected.closest('.quiz-option');
        if (Number(selected.value) === answer) {
          correctCount += 1;
          option.classList.add('is-correct');
        } else {
          option.classList.add('is-wrong');
        }
      }
      if (explanation) explanation.hidden = false;
    });
    var score = document.getElementById('quiz-score');
    if (score) score.textContent = 'Você acertou ' + correctCount + ' de ' + questions.length + ' questões.';
    button.textContent = 'Refazer correção';
  });
}

function iniciarFlashcards() {
  var study = document.getElementById('flashcard-study');
  if (!study) return;
  var cards = Array.prototype.slice.call(study.querySelectorAll('.flashcard-face'));
  var index = 0;
  var previous = document.getElementById('flashcard-prev');
  var next = document.getElementById('flashcard-next');
  var flip = document.getElementById('flashcard-flip');
  var position = document.getElementById('flashcard-position');
  function showCard() {
    cards.forEach(function (card, cardIndex) {
      card.classList.toggle('is-hidden', cardIndex !== index);
      var answer = card.querySelector('.flashcard-answer');
      if (answer) answer.hidden = true;
    });
    if (position) position.textContent = String(index + 1);
    if (previous) previous.disabled = index === 0;
    if (next) next.disabled = index === cards.length - 1;
    if (flip) flip.textContent = 'Mostrar resposta';
  }
  if (previous) previous.addEventListener('click', function () { if (index > 0) { index -= 1; showCard(); } });
  if (next) next.addEventListener('click', function () { if (index < cards.length - 1) { index += 1; showCard(); } });
  if (flip) flip.addEventListener('click', function () {
    var answer = cards[index].querySelector('.flashcard-answer');
    answer.hidden = !answer.hidden;
    flip.textContent = answer.hidden ? 'Mostrar resposta' : 'Esconder resposta';
    if (!answer.hidden) answer.querySelectorAll('[data-markdown]').forEach(renderMarkdownElement);
  });
}

function revelarResposta(button) {
  var card = button.closest('.exercicio-card');
  var answer = card && card.querySelector('.exercicio-resposta');
  if (!answer) return;
  answer.style.display = answer.style.display === 'block' ? 'none' : 'block';
  button.textContent = answer.style.display === 'block' ? 'Esconder resposta' : 'Ver resposta';
}
