"""
Luna — Chatbot educacional inteligente baseado em regras e palavras-chave.
Sem APIs externas. Funciona completamente offline.
"""
import random
import re


class Luna:
    def __init__(self, nome_aluno="estudante", serie=""):
        self.nome = nome_aluno.split()[0] if nome_aluno else "estudante"
        self.serie = serie

    # ── Utilitários ──────────────────────────────────────────────────────
    def _normalizar(self, texto):
        texto = texto.lower()
        texto = re.sub(r'[áàãâä]', 'a', texto)
        texto = re.sub(r'[éèêë]', 'e', texto)
        texto = re.sub(r'[íìîï]', 'i', texto)
        texto = re.sub(r'[óòõôö]', 'o', texto)
        texto = re.sub(r'[úùûü]', 'u', texto)
        texto = re.sub(r'[ç]', 'c', texto)
        return texto

    def _contem(self, texto, palavras):
        t = self._normalizar(texto)
        return any(p in t for p in palavras)

    def _escolher(self, lista):
        return random.choice(lista)

    # ── Base de conhecimento ─────────────────────────────────────────────
    def _detectar_materia(self, texto):
        t = self._normalizar(texto)
        if any(p in t for p in ['matematica', 'fracao', 'equacao', 'numero', 'soma',
                                  'subtracao', 'multiplicacao', 'divisao', 'geometria',
                                  'algebra', 'calculo', 'porcentagem', 'regra de tres',
                                  'conta', 'matematico']):
            return 'matematica'
        if any(p in t for p in ['portugues', 'redacao', 'gramatica', 'verbo', 'sujeito',
                                  'predicado', 'pontuacao', 'ortografia', 'texto', 'leitura',
                                  'sinonimo', 'antonimo', 'crase', 'virgula']):
            return 'portugues'
        if any(p in t for p in ['ciencias', 'celula', 'fotossintese', 'corpo humano', 'biologia',
                                  'quimica', 'fisica', 'atomo', 'molecula', 'ecossistema',
                                  'respiracao', 'digestao', 'orgao', 'planta', 'animal']):
            return 'ciencias'
        if any(p in t for p in ['historia', 'guerra', 'revolucao', 'imperio', 'colonizacao',
                                  'escravidao', 'republica', 'monarquia', 'antigo', 'medieval',
                                  'moderno', 'contemporaneo', 'brasil colonia', 'ditadura']):
            return 'historia'
        if any(p in t for p in ['geografia', 'mapa', 'bioma', 'clima', 'regiao', 'continente',
                                  'pais', 'capital', 'rio', 'montanha', 'floresta', 'cerrado',
                                  'amazonia', 'latitude', 'longitude', 'fuso']):
            return 'geografia'
        if any(p in t for p in ['ingles', 'english', 'vocabulario', 'verb', 'tense', 'pronoun',
                                  'traducao', 'palavra', 'frase em ingles', 'presente', 'passado']):
            return 'ingles'
        return None

    # ── Respostas por matéria ────────────────────────────────────────────
    def _resposta_matematica(self, texto):
        t = self._normalizar(texto)

        if any(p in t for p in ['fracao', 'fração']):
            return self._escolher([
                f"Fração é mais fácil do que parece, {self.nome}! 🍕 Imagina uma pizza inteira. Se você dividir em 4 pedaços e comer 1, você comeu 1/4 da pizza. O número de baixo (denominador) é o total de partes, e o de cima (numerador) é quantas você tem. Faz sentido?",
                f"Pensa assim, {self.nome}: você tem uma barra de chocolate com 10 quadradinhos. Se você comer 3, comeu 3/10 do chocolate. Fração é só isso: uma parte do todo! 🍫",
            ])
        if any(p in t for p in ['porcentagem', '%', 'desconto']):
            return self._escolher([
                f"Porcentagem é super útil no dia a dia, {self.nome}! 🛍️ Quando uma loja diz '30% de desconto', significa que de cada R$100 você economiza R$30. Para calcular: multiplica o valor pelo percentual e divide por 100. Ex: 30% de R$80 = (80 × 30) ÷ 100 = R$24 de desconto!",
                f"Sabe aquela promoção de 50% off? {self.nome}, é literalmente metade do preço! Porcentagem = 'por cento' = de cada 100. 10% = 10 de cada 100 = 0,10. Multiplica o valor por 0,10 e pronto! 💡",
            ])
        if any(p in t for p in ['equacao', 'x', 'incognita', 'variavel']):
            return self._escolher([
                f"Equação é como um jogo de descobrir o número escondido, {self.nome}! 🔍 Se eu digo 'x + 5 = 12', estou perguntando: qual número somado com 5 dá 12? Você pensa: 12 - 5 = 7. Então x = 7! É sempre isso: isole o x fazendo a operação inversa.",
                f"Pensa numa balança, {self.nome}! ⚖️ Uma equação é exatamente isso: dois lados que precisam ficar equilibrados. Se você adiciona algo de um lado, precisa fazer o mesmo do outro. Daí o truque de 'passar pra lá mudando o sinal'!",
            ])
        if any(p in t for p in ['geometria', 'area', 'perimetro', 'triangulo', 'quadrado', 'circulo']):
            return self._escolher([
                f"Geometria está em todo lugar, {self.nome}! 📐 A área de um retângulo (como um quarto) é base × altura. Se seu quarto tem 4m de largura e 5m de comprimento, a área é 4 × 5 = 20m². É exatamente isso que o azulejista calcula antes de azulejar!",
                f"Vou te dar um exemplo real, {self.nome}! 🏠 O perímetro é o contorno total — como se você fosse cercar um terreno. Um terreno 10m × 8m precisa de 10+8+10+8 = 36m de cerca. Área é o espaço interno: 10×8 = 80m².",
            ])
        if any(p in t for p in ['regra de tres', 'proporcao', 'proporcional']):
            return self._escolher([
                f"Regra de três é pra resolver comparações, {self.nome}! 🚗 Exemplo: se um carro percorre 100km com 10 litros, quantos litros para 250km? Monta a proporção: 100 → 10, 250 → x. Multiplica em cruz: x = (250 × 10) ÷ 100 = 25 litros. Simples assim!",
            ])
        # Genérico matemática
        return self._escolher([
            f"Matemática parece difícil mas tem a ver com o mundo real, {self.nome}! 💡 Me conta mais especificamente o que está te deixando com dúvida — pode ser fração, equação, geometria, porcentagem... Quanto mais detalhes, melhor eu consigo te ajudar!",
            f"Boa pergunta sobre matemática, {self.nome}! 🔢 Qual parte está te confundindo? Conta pra mim que eu explico com um exemplo do dia a dia!",
        ])

    def _resposta_portugues(self, texto):
        t = self._normalizar(texto)

        if any(p in t for p in ['redacao', 'texto', 'escrever', 'escrita', 'dissertacao']):
            return self._escolher([
                f"Redação fica muito mais fácil com uma estrutura, {self.nome}! ✍️ Pensa assim: INTRODUÇÃO (apresente o tema e diga o que vai defender), DESENVOLVIMENTO (2 parágrafos com argumentos + exemplos reais), CONCLUSÃO (retome a ideia e dê uma solução ou reflexão). É como construir uma casa: você precisa de fundação, paredes e telhado!",
                f"Pra escrever bem, {self.nome}, o segredo é: 1️⃣ Leia o tema com atenção. 2️⃣ Anote 3 argumentos. 3️⃣ Escreva 1 exemplo real pra cada argumento. 4️⃣ Conecte tudo com palavras como 'portanto', 'além disso', 'no entanto'. Prático demais, né?",
            ])
        if any(p in t for p in ['crase', 'acento grave', 'a ou a']):
            return self._escolher([
                f"Crase é simples, {self.nome}! Regra rápida: substitua a palavra feminina por uma masculina equivalente. Se couber 'ao', coloca crase (à). Ex: 'Vou À escola' → 'Vou AO colégio'. Funcionou? Então tem crase! 🎯",
                f"Macete da crase, {self.nome}! ✅ Crase só acontece antes de palavras FEMININAS. Teste: 'Fui à cidade' → troca por 'Fui ao bairro' → 'ao' cabe? Sim! Então tem crase. 'Fui à tarde' → 'Fui ao fim da tarde' → cabe! Tem crase. Fácil né? 😄",
            ])
        if any(p in t for p in ['verbo', 'conjugacao', 'tempo verbal', 'passado', 'futuro']):
            return self._escolher([
                f"Verbos são as ações da frase, {self.nome}! 🏃 'Correr', 'estudar', 'comer' são verbos no infinitivo. Quando conjugamos, mostramos quem faz e quando. Ex: EU corro (presente), EU corri (passado), EU correrei (futuro). Pensa no tempo como uma linha do tempo mesmo!",
            ])
        if any(p in t for p in ['sujeito', 'predicado', 'frase', 'oracao', 'sintaxe']):
            return self._escolher([
                f"Sujeito é de quem ou do que a frase fala, {self.nome}! 🎯 Na frase 'A Luna explica bem', o sujeito é 'A Luna'. O predicado é o resto: 'explica bem'. Dica: pergunte 'quem?' ou 'o que?' para o verbo — a resposta é o sujeito!",
            ])
        return self._escolher([
            f"Português tem muitos temas, {self.nome}! 📝 Posso te ajudar com redação, gramática, interpretação de texto, verbos, crase, pontuação... O que está te dando mais trabalho agora?",
            f"Me conta mais, {self.nome}! 📖 Português é poderoso — com ele você se comunica, argumenta e conta histórias. Me diz se a dúvida é em gramática, escrita ou leitura que eu te explico de um jeito simples!",
        ])

    def _resposta_ciencias(self, texto):
        t = self._normalizar(texto)

        if any(p in t for p in ['fotossintese', 'fotossíntese', 'planta', 'clorofila']):
            return self._escolher([
                f"Fotossíntese é o 'almoço' das plantas, {self.nome}! 🌱☀️ Enquanto a gente come comida pra ter energia, a planta usa LUZ DO SOL + ÁGUA + GÁS CARBÔNICO pra fabricar o próprio alimento (glicose). E o melhor: ela 'bota fora' o oxigênio — que a gente respira! É basicamente uma fábrica de ar limpo.",
                f"Pensa assim, {self.nome}: a planta é como um painel solar! ☀️ Ela capta a energia do sol pela clorofila (que deixa as folhas verdes) e transforma em açúcar pra se alimentar. O oxigênio que ela libera é o 'resíduo' desse processo — e que resíduo bom pra gente!",
            ])
        if any(p in t for p in ['celula', 'celulas', 'nucleo', 'membrana', 'organela']):
            return self._escolher([
                f"A célula é a unidade básica da vida, {self.nome}! 🔬 Pensa nela como uma fábrica: o NÚCLEO é a sala de controle (guarda o DNA), a MEMBRANA é o muro da fábrica (controla o que entra e sai), e as ORGANELAS são os departamentos (cada um com sua função). Seu corpo inteiro é feito de trilhões dessas 'fábricas'!",
            ])
        if any(p in t for p in ['corpo humano', 'orgao', 'coração', 'pulmao', 'figado', 'rim']):
            return self._escolher([
                f"O corpo humano é incrível, {self.nome}! 💪 Pensa em cada órgão como uma parte de uma fábrica enorme: o CORAÇÃO é a bomba d'água (bombeia sangue), os PULMÕES são o sistema de ventilação (trocam gases), o FÍGADO é a central de processamento (filtra toxinas), os RINS são o sistema de esgoto (filtram o sangue e fazem urina). Tudo conectado!",
            ])
        if any(p in t for p in ['atomo', 'molecula', 'elemento', 'quimica', 'tabela periodica']):
            return self._escolher([
                f"Átomo é o 'tijolo' de tudo que existe, {self.nome}! ⚛️ A água (H₂O) é feita de 2 átomos de Hidrogênio + 1 de Oxigênio. Quando átomos se juntam, formam moléculas. E moléculas formam tudo: você, o ar, a cadeira... É tudo química!",
            ])
        return self._escolher([
            f"Ciências explica como o mundo funciona, {self.nome}! 🔬 Posso te ajudar com células, fotossíntese, corpo humano, ecossistemas, átomos, física básica... Qual tema está estudando agora?",
            f"Boa pergunta de ciências, {self.nome}! 🌍 Me conta o que está estudando — biologia, química ou física — que eu explico com exemplos do dia a dia!",
        ])

    def _resposta_historia(self, texto):
        t = self._normalizar(texto)

        if any(p in t for p in ['brasil colonia', 'colonizacao', 'colonizacao', 'portugues no brasil', 'descobrimento']):
            return self._escolher([
                f"O Brasil Colônia foi um período longo e complexo, {self.nome}! 🇧🇷 De 1500 a 1822, Portugal controlava o Brasil e usava suas riquezas (pau-brasil, ouro, açúcar). Os indígenas foram explorados e os africanos foram trazidos como escravizados. É o período que formou muito da nossa cultura atual — nosso idioma, religião e até parte da culinária vem daí.",
            ])
        if any(p in t for p in ['escravidao', 'escravizados', 'africanos', 'abolição']):
            return self._escolher([
                f"A escravidão no Brasil durou mais de 300 anos, {self.nome} — foi uma das maiores e mais longas da história. 😔 Africanos eram arrancados de suas terras, famílias separadas, e forçados a trabalhar sem direitos. A resistência nunca parou: Quilombo dos Palmares, revoltas, fugas. A abolição formal veio em 1888 com a Lei Áurea, mas sem indenização ou integração — o que explica desigualdades que existem até hoje.",
            ])
        if any(p in t for p in ['segunda guerra', 'segunda guerra mundial', 'hitler', 'nazismo', 'holocausto']):
            return self._escolher([
                f"A 2ª Guerra Mundial (1939-1945) foi o conflito mais devastador da história, {self.nome}. 🌍 O nazismo de Hitler pregava superioridade racial e levou ao Holocausto (extermínio de ~6 milhões de judeus e outros grupos). O Brasil entrou na guerra em 1944. O resultado: criação da ONU, Guerra Fria e reconfiguração do mundo que ainda sentimos hoje.",
            ])
        if any(p in t for p in ['revolucao industrial', 'industria', 'maquina a vapor']):
            return self._escolher([
                f"A Revolução Industrial (séc. XVIII, Inglaterra) mudou TUDO, {self.nome}! 🏭 Antes, as coisas eram feitas à mão. Com as máquinas a vapor, a produção explodiu. Mas as condições de trabalho eram horríveis: crianças trabalhavam em fábricas, 16h por dia, sem segurança. Daí surgiram os sindicatos e os direitos trabalhistas — que a gente tem até hoje!",
            ])
        return self._escolher([
            f"História conecta o passado com o presente, {self.nome}! 📜 Me conta qual período ou tema você está estudando — Pré-história, Antiga, Medieval, Moderna, Contemporânea, Brasil Colônia, República... Que eu explico com contexto!",
            f"Boa área para explorar, {self.nome}! 🏛️ História nos ajuda a entender por que o mundo é como é hoje. Qual período ou tema está te deixando confuso?",
        ])

    def _resposta_geografia(self, texto):
        t = self._normalizar(texto)

        if any(p in t for p in ['bioma', 'floresta amazonica', 'cerrado', 'caatinga', 'pantanal', 'mata atlantica']):
            return self._escolher([
                f"O Brasil tem 6 biomas principais, {self.nome}! 🌿 A AMAZÔNIA é a maior floresta tropical do mundo (norte do Brasil). O CERRADO é o 'berço das águas' (centro-oeste). A CAATINGA é semiárida e exclusiva do Brasil (nordeste). A MATA ATLÂNTICA é a mais ameaçada (litoral). O PAMPA fica no RS. E o PANTANAL é a maior planície alagável do mundo. Cada um tem fauna e flora únicas!",
            ])
        if any(p in t for p in ['clima', 'temperatura', 'tropical', 'subtropical', 'chuva']):
            return self._escolher([
                f"O clima de um lugar depende de vários fatores, {self.nome}! 🌤️ Latitude (distância do Equador), altitude (quanto mais alto, mais frio) e proximidade do mar. O Brasil tem clima tropical na maior parte — quente e chuvoso. O sul tem subtropical (4 estações mais definidas). É por isso que em janeiro no RS pode fazer frio e no Amazonas é quente o ano todo!",
            ])
        if any(p in t for p in ['continente', 'pais', 'capital', 'mapa', 'regiao']):
            return self._escolher([
                f"Vamos situar no mapa, {self.nome}! 🗺️ O mundo tem 7 continentes: Américas (Norte e Sul), Europa, África, Ásia, Oceania e Antártida. O Brasil está na América do Sul e faz fronteira com quase todos os países do continente (exceto Chile e Equador). Qual região ou país você precisa estudar?",
            ])
        if any(p in t for p in ['latitude', 'longitude', 'fuso', 'meridianos', 'paralelos']):
            return self._escolher([
                f"Latitude e longitude são as 'coordenadas' do GPS da Terra, {self.nome}! 📍 LATITUDE mede o quanto você está distante do Equador (norte ou sul). LONGITUDE mede o quanto está distante do Meridiano de Greenwich (leste ou oeste). Juntas, essas duas coordenadas localizam qualquer ponto do planeta — exatamente como o GPS do celular!",
            ])
        return self._escolher([
            f"Geografia explica o espaço onde vivemos, {self.nome}! 🌍 Posso te ajudar com biomas, climas, regiões do Brasil, continentes, cartografia... O que você está estudando agora?",
        ])

    def _resposta_ingles(self, texto):
        t = self._normalizar(texto)

        if any(p in t for p in ['simple present', 'presente simples', 'verbo no presente', 'rotina']):
            return self._escolher([
                f"Simple Present é pra falar de rotinas e fatos, {self.nome}! 📅 Ex: 'I study every day' (Eu estudo todo dia). Com he/she/it, adiciona -s ao verbo: 'She studies'. Negativa: 'I don't study on Sunday'. Pergunta: 'Do you study English?' — Dica: use pra contar sua rotina em inglês!",
            ])
        if any(p in t for p in ['past simple', 'passado simples', 'verbo no passado', 'ontem']):
            return self._escolher([
                f"Past Simple é pra falar do que JÁ aconteceu, {self.nome}! ⏮️ Verbos regulares ganham -ed: 'study → studied', 'play → played'. Verbos irregulares são decoreba: 'go → went', 'eat → ate', 'see → saw'. Negativa: 'I didn't go'. Pergunta: 'Did you study?' Muito usado em histórias e diários!",
            ])
        if any(p in t for p in ['vocabulario', 'palavra', 'traducao', 'significa', 'ingles']):
            return self._escolher([
                f"Vou te ajudar com vocabulário, {self.nome}! 📚 Dica de ouro: aprenda palavras em contexto, não isoladas. Em vez de decorar 'apple = maçã', pensa: 'An apple a day keeps the doctor away' (Uma maçã por dia mantém o médico longe). Qual palavra ou tema você quer aprender?",
                f"Vocabulário em inglês fica mais fácil com música e séries, {self.nome}! 🎵 Muitas palavras do inglês já estão no nosso dia a dia: 'selfie', 'download', 'smartphone', 'online'. Qual área você quer expandir — escola, tecnologia, esportes?",
            ])
        if any(p in t for p in ['pronome', 'pronoun', 'i you he she']):
            return self._escolher([
                f"Os pronomes em inglês são poucos e simples, {self.nome}! 👤 I (eu), You (você/tu), He (ele), She (ela), It (ele/ela para coisas/animais), We (nós), You (vocês), They (eles/elas). A diferença do português: não tem 'o' e 'a' — tudo vira 'it' quando não é pessoa!",
            ])
        return self._escolher([
            f"Inglês é uma porta para o mundo, {self.nome}! 🌐 Posso te ajudar com gramática (tempos verbais, pronomes), vocabulário, interpretação de texto... O que você precisa agora?",
            f"Let's study English, {self.nome}! 😄 Me conta o que está estudando — pode ser Present Simple, Past Simple, vocabulário, leitura... Vamos juntos!",
        ])

    # ── Intenções gerais ─────────────────────────────────────────────────
    def _resposta_saudacao(self):
        return self._escolher([
            f"Oi, {self.nome}! 👋 Que ótimo te ver por aqui! Sou a Luna, sua assistente de estudos. Pode me perguntar sobre qualquer matéria — Matemática, Português, Ciências, História, Geografia ou Inglês. O que vamos estudar hoje?",
            f"Olá, {self.nome}! 😊 Estou aqui pra te ajudar a entender qualquer coisa que pareça difícil. Me conta: o que está te deixando com dúvida?",
            f"Oi, {self.nome}! 🌟 Bem-vindo de volta! Pronto(a) para aprender algo novo hoje? Me pergunta o que quiser!",
        ])

    def _resposta_confuso(self):
        return self._escolher([
            f"Não se preocupe, {self.nome}! Isso é completamente normal. 💙 Vamos por partes — me conta exatamente qual parte você não entendeu e eu explico de um jeito mais simples, com um exemplo do dia a dia.",
            f"Respira, {self.nome}! 😌 Ninguém nasce sabendo. Me diz qual foi a parte que travou e vamos descomplicar juntos!",
            f"Tá, {self.nome}, sem pressão! 🤝 Aprender leva tempo. Me conta de novo o que você entendeu até agora e onde ficou a dúvida — assim eu sei o melhor jeito de explicar pra você.",
        ])

    def _resposta_motivacao(self):
        return self._escolher([
            f"Você está no caminho certo só de estar aqui estudando, {self.nome}! 💪 Cada dúvida que você tira é um passo a mais. Continue assim!",
            f"{self.nome}, estudar é o melhor investimento que você pode fazer em si mesmo(a)! 🌟 Pode não parecer agora, mas cada coisa que você aprende hoje vai fazer diferença no futuro. Vai com tudo!",
            f"Acredita em você, {self.nome}! 🚀 Dificuldade é sinal de crescimento — se fosse fácil, você não estaria aprendendo nada novo. Continua!",
        ])

    def _resposta_exercicio(self, materia_contexto):
        exercicios = {
            'matematica': [
                f"Exercício de Matemática pra você, {self.nome}! 📝\n\nUma camisa custa R$80. Tem 25% de desconto. Qual o valor final?\n\n💡 Dica: calcule 25% de 80 e subtraia.\n\n||Resposta: 25% de 80 = 20. R$80 - R$20 = R$60||",
                f"Tenta esse, {self.nome}! 🔢\n\nSe uma bicicleta percorre 15km em 1 hora, quanto percorre em 3h30min?\n\n💡 Dica: 3h30min = 3,5 horas.\n\n||Resposta: 15 × 3,5 = 52,5 km||",
            ],
            'portugues': [
                f"Exercício de Português, {self.nome}! ✍️\n\nIdentifique o sujeito e predicado:\n'Os alunos estudaram muito para a prova.'\n\n💡 Pergunta: Quem estudou muito?\n\n||Resposta: Sujeito = 'Os alunos' | Predicado = 'estudaram muito para a prova'||",
            ],
            'ciencias': [
                f"Exercício de Ciências, {self.nome}! 🔬\n\nVerdadeiro ou Falso: 'As plantas absorvem oxigênio do ar durante a fotossíntese.'\n\n💡 Lembra o que a planta usa como matéria-prima?\n\n||Resposta: FALSO! As plantas absorvem CO₂ (gás carbônico), não oxigênio. Elas LIBERAM oxigênio!||",
            ],
            'historia': [
                f"Exercício de História, {self.nome}! 📜\n\nEm que ano foi proclamada a República do Brasil e quem foi o primeiro presidente?\n\n💡 Fim do Império, início da República...\n\n||Resposta: 1889. Primeiro presidente: Deodoro da Fonseca (proclamador) e depois Floriano Peixoto.||",
            ],
            'geografia': [
                f"Exercício de Geografia, {self.nome}! 🌍\n\nQual é o maior bioma do Brasil em extensão territorial?\n\n💡 Pensa no norte do país...\n\n||Resposta: Amazônia — ocupa cerca de 49% do território brasileiro!||",
            ],
            'ingles': [
                f"English exercise for you, {self.nome}! 🌐\n\nComplete: 'She ___ (study) English every day.'\n\n💡 Simple Present com she/he/it...\n\n||Resposta: She STUDIES English every day. (3ª pessoa → adiciona -ies quando termina em y)||",
            ],
        }
        mat = materia_contexto or 'matematica'
        lista = exercicios.get(mat, exercicios['matematica'])
        return self._escolher(lista)

    def _resposta_agradecimento(self):
        return self._escolher([
            f"De nada, {self.nome}! 😊 É pra isso que estou aqui. Qualquer outra dúvida, pode perguntar!",
            f"Fico feliz em ajudar, {self.nome}! 💙 Continua estudando — você está indo muito bem!",
            f"Sempre, {self.nome}! 🌟 Se tiver mais dúvidas, pode chamar a hora que quiser!",
        ])

    def _resposta_nome(self):
        return self._escolher([
            f"Me chamo Luna! 🌙 Sou sua assistente de estudos, aqui pra te ajudar a entender qualquer matéria de um jeito simples e prático. O nome Luna vem da lua — assim como a lua ilumina a noite, eu quero iluminar seus estudos! ✨",
            f"Sou a Luna! 😊 Fui criada pra ser sua parceira de estudos — paciente, clara e sempre com um exemplo prático. Pode me perguntar qualquer coisa sobre as matérias!",
        ])

    def _resposta_padrao(self):
        return self._escolher([
            f"Hmm, não tenho certeza se entendi bem, {self.nome}. 🤔 Você pode reformular a pergunta? Consigo te ajudar melhor com temas de Matemática, Português, Ciências, História, Geografia e Inglês!",
            f"Interessante, {self.nome}! Mas preciso de mais detalhes. 💭 Qual matéria ou tema você quer explorar? Estou pronta pra explicar com exemplos práticos!",
            f"Não tenho certeza do que você quer dizer, {self.nome}. 😅 Me conta mais — qual matéria está estudando e qual dúvida específica você tem?",
        ])

    # ── Método principal ─────────────────────────────────────────────────
    def responder(self, mensagem, materia_contexto=None):
        t = self._normalizar(mensagem)

        # Saudações
        if self._contem(t, ['oi', 'ola', 'olá', 'hey', 'bom dia', 'boa tarde', 'boa noite', 'oi luna', 'ola luna']):
            return self._resposta_saudacao()

        # Nome da Luna
        if self._contem(t, ['seu nome', 'quem e voce', 'quem e vc', 'o que voce e', 'o que e voce', 'como voce se chama']):
            return self._resposta_nome()

        # Agradecimentos
        if self._contem(t, ['obrigado', 'obrigada', 'valeu', 'muito obrigado', 'thanks', 'thank you', 'vlw']):
            return self._resposta_agradecimento()

        # Motivação / frustração
        if self._contem(t, ['motivacao', 'motivar', 'nao consigo', 'desistir', 'cansado de estudar', 'dificil demais', 'impossivel']):
            return self._resposta_motivacao()

        # Confusão
        if self._contem(t, ['nao entendi', 'nao entendo', 'confuso', 'nao sei', 'nao compreendi', 'ficou confuso', 'nao faz sentido', 'complicado']):
            return self._resposta_confuso()

        # Exercício
        if self._contem(t, ['exercicio', 'questao', 'atividade', 'prova', 'teste', 'treinar', 'praticar', 'me da uma questao', 'me da um exercicio']):
            materia = materia_contexto or self._detectar_materia(mensagem)
            return self._resposta_exercicio(materia)

        # Detecta matéria e responde
        materia = materia_contexto or self._detectar_materia(mensagem)
        if materia == 'matematica':
            return self._resposta_matematica(mensagem)
        if materia == 'portugues':
            return self._resposta_portugues(mensagem)
        if materia == 'ciencias':
            return self._resposta_ciencias(mensagem)
        if materia == 'historia':
            return self._resposta_historia(mensagem)
        if materia == 'geografia':
            return self._resposta_geografia(mensagem)
        if materia == 'ingles':
            return self._resposta_ingles(mensagem)

        # Resposta padrão
        return self._resposta_padrao()

    def mensagem_boas_vindas(self):
        return (
            f"Oi, {self.nome}! 👋 Sou a **Luna**, sua assistente de estudos.\n\n"
            f"Estou aqui pra te ajudar a entender qualquer matéria de um jeito simples, "
            f"com exemplos do dia a dia. Pode me perguntar sobre:\n\n"
            f"📝 Português · 🔢 Matemática · 🔬 Ciências\n"
            f"📚 História · 🌍 Geografia · 🌐 Inglês\n\n"
            f"O que vamos estudar hoje?"
        )
