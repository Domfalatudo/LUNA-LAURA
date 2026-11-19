# 🌙 Luna — Sistema Educacional com IA
**TCC — Ensino Técnico Profissionalizante | Componente: Inteligência Artificial**
**Tema: Desenvolvimento Escolar**

---

## O que é
Sistema web educacional completo com:
- 🌙 **Luna** — chatbot de estudos inteligente com exemplos práticos e do cotidiano
- 🏠 **Página inicial** — apresenta a proposta e direciona para cadastro ou login
- 📊 **Dashboard pessoal** — mostra somente matérias e notas que você cadastrar; não inventa médias ou frequência
- 🗂️ **Caderno de notas** — adicione matérias, avaliações, notas e datas; remova registros quando necessário
- 👤 **Perfil** — atualize seu nome e série, altere a senha ou exclua sua conta e seus dados
- 🧭 **Navegação e animações** — acesso rápido às páginas, com suporte a preferência por movimento reduzido
- 🔐 **Login individual** — cada aluno tem sua conta com série e histórico
- 📚 **6 matérias** — conteúdo, exercícios e chat contextual por matéria
- 💬 **Histórico de conversas** — salvo por conta, com opção de criar, limpar e excluir conversas
- 📝 **Ações pela Luna** — registre/edite notas e organize matérias pedindo no chat
- ✧ **Quizzes e flashcards** — materiais gerados por IA e guardados numa biblioteca pessoal
- ◷ **Rotina diária** — registre sessões, acompanhe sua meta e personalize as respostas da Luna
- ∑ **Fórmulas legíveis** — respostas com Markdown e equações renderizadas no chat
- 🤖 **IA de classificação** — K-NN implementado do zero para prever desempenho
- 🎨 **Design minimalista** — interface preto e branco, limpa e responsiva

> O classificador K-NN continua disponível separadamente no terminal para fins didáticos e usa o conjunto de exemplos `dados/alunos.csv`; ele não é mostrado como uma avaliação pessoal no dashboard. A Luna pode responder usando a Groq pela API ou, se não houver chave configurada, seu modo offline baseado em regras.

---

## Pré-requisitos
- Python 3.7 ou superior
- Flask e python-dotenv

## Instalação e execução

### No VS Code

Abra a pasta do projeto no VS Code e pressione **F5**. Escolha **Luna (Flask)** para iniciar o site ou **IA Escolar (terminal)** para executar o classificador. O projeto seleciona o ambiente Python `.venv` automaticamente.

Para ativar a IA da Groq e manter as chaves locais no arquivo `.env`:

1. Crie uma chave na plataforma oficial da Groq.
2. Copie `.env.example` para `.env` na pasta do projeto.
3. Substitua `cole_sua_chave_aqui` por uma chave da Groq e defina `FLASK_SECRET_KEY`. Para gerar esta última, execute `.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"` e cole o resultado.
4. O `.env` é ignorado pelo Git; não compartilhe nem publique esse arquivo.
5. Reinicie o servidor. O chat mostrará **Groq conectada** quando a chave estiver configurada. Sem chave, continua funcionando no modo offline.

O uso da API depende dos limites e preços vigentes na conta Groq; não há garantia de uso gratuito. As mensagens do chat são enviadas ao serviço para gerar respostas, então não envie dados pessoais. Se a API falhar, a Luna informa o erro e não troca silenciosamente para uma resposta offline.

### Pelo terminal

1. Abra o terminal na pasta do projeto:
   ```
   cd C:\Users\domfa\OneDrive\Documentos\Laura\projeto_ia_escolar
   ```
2. Se necessário, instale as dependências no ambiente do projeto:
   ```
   .venv\Scripts\python.exe -X utf8 -m pip install -r requirements.txt
   ```
3. Execute o servidor Flask:
   ```
   .venv\Scripts\python.exe -X utf8 app.py
   ```
4. Abra **http://localhost:5000** no navegador. Não abra os arquivos HTML diretamente: as páginas e o CSS são servidos pelo Flask.

Para executar o classificador pelo terminal:

```
.venv\Scripts\python.exe -X utf8 ia_escolar.py
```

## Publicar na Vercel

O projeto usa Flask e a Vercel detecta automaticamente o `app` definido em `app.py` como uma função Python. Importe este repositório na Vercel; não é necessário iniciar `app.run()` no deploy.

Configure estas variáveis em **Project Settings → Environment Variables**:

- `FLASK_SECRET_KEY`: segredo aleatório e exclusivo para as sessões de produção.
- `GROQ_API_KEY`: chave da API, se quiser ativar a Groq.
- `GROQ_MODEL`: opcional; se omitida, usa `openai/gpt-oss-20b`.

Não publique o arquivo `.env`. O CSS e o JavaScript são servidos a partir de `public/` pela Vercel.

**Atenção: a versão atual usa armazenamento temporário em `/tmp` na Vercel.** Cadastros, notas, conversas e materiais de estudo podem desaparecer entre execuções ou instâncias; isso serve somente para demonstração e não é adequado para dados reais. Para persistência em produção, substitua `dados/usuarios.json` por um banco de dados persistente antes de publicar para usuários reais.

## Contas e dados

Crie uma conta na tela de login → "Criar conta". Contas novas começam sem matérias nem notas preenchidas; você pode adicioná-las em **Minhas matérias** ou pedir à Luna para fazê-lo. Conversas, notas, quizzes, flashcards e preferências ficam associados à conta em `dados/usuarios.json` no uso local; o histórico permanece até você excluir a conversa. Esse arquivo não deve ser compartilhado nem enviado ao GitHub. Ao entrar em contas antigas, a senha em texto simples é migrada para armazenamento protegido e as notas antigas de exemplo são descartadas para não aparecerem como dados reais.

Use **Meu perfil** para alterar a senha ou excluir permanentemente a conta. A exclusão pede a senha e a confirmação explícita `EXCLUIR`.

---

## Classificador didático (`ia_escolar.py`)

1. **Carrega os dados** do arquivo CSV
2. **Pré-processa e normaliza** as features
3. **Treina o modelo K-NN** com 80% dos dados
4. **Avalia o modelo** com 20% dos dados (acurácia, F1, matriz de confusão)
5. **Executa os 5 casos de teste** documentados
6. **Abre o menu interativo** para previsão de novos alunos

Essas estimativas são demonstrativas e não alimentam as notas nem o dashboard da conta.

---

## Exemplo de uso (previsão de novo aluno)

```
Escolha: 1

══════════════════════════════════════════════
  PREVISÃO PARA NOVO ALUNO
══════════════════════════════════════════════
Nome do aluno: Maria
Nota em Português  (0–10): 5.5
Nota em Matemática (0–10): 4.0
Nota em Ciências   (0–10): 6.0
Nota em História   (0–10): 5.0
Frequência (%)          : 72
Horas de estudo/semana  : 4
Participação (baixa/media/alta): media
Situação familiar (estavel/instavel): estavel

── Resultado para Maria ──
  Média geral          : 5.13
  Frequência           : 72.0%
  Modelo K-NN (k=5)   : RISCO
  Sistema de Regras    : RISCO
  Justificativa regras : Frequência 72.0% na zona de atenção (60–74%)

── Recomendação Pedagógica ──
  ⚠  Aluno em zona de atenção.
     → Monitorar evolução nas próximas semanas.
     → Oferecer suporte pedagógico preventivo.
```

---

## Dependências (bibliotecas)
| Módulo | Uso | Nativo? |
|---|---|---|
| `csv` | Leitura do arquivo de dados | ✅ Python padrão |
| `math` | Cálculo da distância euclidiana | ✅ Python padrão |
| `random` | Embaralhamento para divisão treino/teste | ✅ Python padrão |
| `collections` | Contagem de votos no K-NN | ✅ Python padrão |
