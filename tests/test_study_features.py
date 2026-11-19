import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app as luna_app


class StudyFeatureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp.name)
        self.users_path = self.data_dir / 'usuarios.json'
        self.data_patch = patch.multiple(
            luna_app,
            DATA_DIR=self.data_dir,
            USUARIOS_PATH=self.users_path,
        )
        self.data_patch.start()
        self.addCleanup(self.data_patch.stop)
        self.addCleanup(self.temp.cleanup)
        luna_app.app.config['TESTING'] = True
        self.addCleanup(lambda: luna_app.app.config.update(TESTING=False))
        luna_app.salvar_usuarios({
            'ana': {
                'nome': 'Ana',
                'serie': '8º ano',
                'senha': 'hash',
                'materias': {'matematica': {'nome': 'Matemática', 'notas': []}},
                'ultimo_acesso': [],
            },
            'bia': {
                'nome': 'Bia',
                'serie': '9º ano',
                'senha': 'hash',
                'materias': {'matematica': {'nome': 'Matemática', 'notas': []}},
                'ultimo_acesso': [],
            },
        })

    def autenticar(self, cliente, chave):
        usuario = luna_app.carregar_usuarios()[chave]
        with cliente.session_transaction() as sessao:
            sessao['user_key'] = chave
            sessao['aluno'] = luna_app.perfil_publico(usuario)
            sessao['csrf_token'] = 'token-teste'

    def test_chat_and_ai_grade_action_are_saved_per_account(self):
        cliente = luna_app.app.test_client()
        self.autenticar(cliente, 'ana')

        def responder(_mensagem, _historico, _materia, _contexto, _preferencias, _ferramentas, executar):
            resultado = executar('registrar_nota', {
                'materia': 'Matemática',
                'valor': 8.5,
                'titulo': 'Prova',
            })
            self.assertTrue(resultado['ok'])
            return 'Nota registrada.'

        with patch.object(luna_app, 'groq_configurada', return_value=True):
            with patch.object(luna_app, 'responder_com_ferramentas', side_effect=responder):
                resposta = cliente.post(
                    '/api/chat',
                    json={'mensagem': 'Registre 8,5 na prova de Matemática'},
                    headers={'X-CSRFToken': 'token-teste'},
                )

        self.assertEqual(resposta.status_code, 200)
        usuarios = luna_app.carregar_usuarios()
        ana = usuarios['ana']
        self.assertEqual(ana['materias']['matematica']['notas'][0]['valor'], 8.5)
        self.assertEqual(len(ana['conversas']), 1)
        self.assertEqual(len(ana['conversas'][0]['mensagens']), 2)
        self.assertEqual(usuarios['bia']['materias']['matematica']['notas'], [])
        self.assertNotIn('conversas', usuarios['bia'])

    def test_conversation_create_and_delete_are_account_scoped(self):
        cliente = luna_app.app.test_client()
        self.autenticar(cliente, 'ana')
        self.assertEqual(cliente.get('/chat').status_code, 200)
        primeira = luna_app.carregar_usuarios()['ana']['conversas'][0]['id']
        nova = cliente.post(
            '/api/chat/conversas', headers={'X-CSRFToken': 'token-teste'}
        )
        self.assertEqual(nova.status_code, 200)
        segunda = nova.get_json()['id']
        excluida = cliente.delete(
            f'/api/chat/conversas/{primeira}',
            headers={'X-CSRFToken': 'token-teste'},
        )
        self.assertEqual(excluida.status_code, 200)
        ana = luna_app.carregar_usuarios()['ana']
        self.assertEqual([item['id'] for item in ana['conversas']], [segunda])

        outro_cliente = luna_app.app.test_client()
        self.autenticar(outro_cliente, 'bia')
        self.assertEqual(outro_cliente.get('/chat').status_code, 200)
        self.assertEqual(len(luna_app.carregar_usuarios()['bia']['conversas']), 1)

    def test_invalid_grade_is_not_saved(self):
        usuarios = luna_app.carregar_usuarios()
        ana = usuarios['ana']
        resultado = luna_app.executar_ferramenta_estudo(
            'ana', ana, 'registrar_nota',
            {'materia': 'Matemática', 'valor': 11},
        )
        self.assertFalse(resultado['ok'])
        self.assertEqual(luna_app.carregar_usuarios()['ana']['materias']['matematica']['notas'], [])

    def test_ai_can_edit_subject_and_grade_records(self):
        ana = luna_app.carregar_usuarios()['ana']
        added = luna_app.executar_ferramenta_estudo(
            'ana', ana, 'registrar_nota',
            {'materia': 'Matemática', 'valor': 7, 'titulo': 'Prova'},
        )
        self.assertTrue(added['ok'])
        edited = luna_app.executar_ferramenta_estudo(
            'ana', ana, 'editar_nota',
            {'materia': 'Matemática', 'indice': 1, 'valor': 9},
        )
        self.assertTrue(edited['ok'])
        renamed = luna_app.executar_ferramenta_estudo(
            'ana', ana, 'renomear_materia',
            {'materia': 'Matemática', 'novo_nome': 'Álgebra'},
        )
        self.assertTrue(renamed['ok'])
        saved = luna_app.carregar_usuarios()['ana']
        self.assertEqual(saved['materias']['algebra']['notas'][0]['valor'], 9)

    def test_new_study_pages_render_for_an_authenticated_account(self):
        cliente = luna_app.app.test_client()
        self.autenticar(cliente, 'ana')
        for path in ('/chat', '/quizzes', '/flashcards', '/configuracoes'):
            with self.subTest(path=path):
                self.assertEqual(cliente.get(path).status_code, 200)

    def test_daily_study_session_updates_dashboard_goal(self):
        cliente = luna_app.app.test_client()
        self.autenticar(cliente, 'ana')
        resposta = cliente.post(
            '/dashboard',
            data={
                'acao': 'registrar_sessao_estudo',
                'minutos': '25',
                'assunto': 'Ondas',
                'csrf_token': 'token-teste',
            },
            follow_redirects=True,
        )
        self.assertEqual(resposta.status_code, 200)
        usuario = luna_app.carregar_usuarios()['ana']
        self.assertEqual(usuario['sessoes_estudo'][-1]['minutos'], 25)
        self.assertEqual(luna_app.minutos_estudados_hoje(usuario), 25)
        self.assertIn(b'25 de 30 minutos estudados', resposta.data)

    def test_generated_quiz_and_flashcards_are_persisted(self):
        usuarios = luna_app.carregar_usuarios()
        ana = usuarios['ana']
        quiz_data = {
            'titulo': 'Frações',
            'questoes': [{
                'pergunta': 'Quanto é 1/2 + 1/2?',
                'opcoes': ['0', '1', '2', '3'],
                'correta': 1,
                'explicacao': 'As metades formam um inteiro.',
            }] * 3,
        }
        cards_data = {
            'titulo': 'Frações básicas',
            'cartoes': [
                {'frente': 'O que é numerador?', 'verso': 'É o número de cima da fração.'}
            ] * 3,
        }
        with patch.object(luna_app, 'gerar_json_groq', side_effect=[quiz_data, cards_data]):
            quiz = luna_app._gerar_quiz('ana', ana, 'matematica', 'frações', 3)
            deck = luna_app._gerar_flashcards('ana', ana, 'matematica', 'frações', 3)

        salvos = luna_app.carregar_usuarios()['ana']
        self.assertEqual(salvos['quizzes'][0]['id'], quiz['id'])
        self.assertEqual(salvos['flashcards'][0]['id'], deck['id'])
        self.assertEqual(len(salvos['quizzes'][0]['questoes']), 3)
        self.assertEqual(len(salvos['flashcards'][0]['cartoes']), 3)
        cliente = luna_app.app.test_client()
        self.autenticar(cliente, 'ana')
        self.assertEqual(cliente.get(f"/quizzes/{quiz['id']}").status_code, 200)
        self.assertEqual(cliente.get(f"/flashcards/{deck['id']}").status_code, 200)

    def test_quiz_validation_rejects_malformed_model_output(self):
        ana = luna_app.carregar_usuarios()['ana']
        with patch.object(luna_app, 'gerar_json_groq', return_value={'questoes': []}):
            with self.assertRaises(luna_app.GroqError):
                luna_app._gerar_quiz('ana', ana, 'matematica', 'frações', 3)
        self.assertEqual(luna_app.carregar_usuarios()['ana'].get('quizzes', []), [])


if __name__ == '__main__':
    unittest.main()
