"""Streamlit页面验收：未配置API时可引导配置、切换页面和创建会话。"""
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch, MagicMock
from streamlit.testing.v1 import AppTest
from config_data import get_settings, ROOT


class FrontendTests(unittest.TestCase):
    def test_setup_navigation_and_sessions(self):
        folder = ROOT / 'tmp' / 'tests'
        folder.mkdir(parents=True, exist_ok=True)
        path = Path(tempfile.mkdtemp(dir=folder))
        settings = replace(get_settings(), api_key='', embedding_key='', history_db=path / 'history.sqlite3')
        with patch('config_data.get_settings', return_value=settings):
            app = AppTest.from_file(str(ROOT / 'app_qa.py'), default_timeout=30).run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.warning), 1)
            self.assertTrue(app.chat_input[0].disabled)
            self.assertEqual(len([x for x in app.button if x.key and x.key.startswith('quick_')]), 6)
            app.sidebar.radio[0].set_value('知识库管理').run()
            self.assertEqual(len(app.exception), 0)
            self.assertIn('知识库管理', [x.value for x in app.title])
            app.sidebar.button[0].click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.sidebar.selectbox[0].options), 2)

    def test_consumer_shortcut_history_and_optional_details(self):
        """快捷咨询走问答服务并保存历史，技术信息默认隐藏；失败不保存假答案。"""
        folder = ROOT / 'tmp' / 'tests'
        folder.mkdir(parents=True, exist_ok=True)
        path = Path(tempfile.mkdtemp(dir=folder))
        settings = replace(get_settings(), api_key='test-chat', embedding_key='test-embedding',
                           history_db=path / 'history.sqlite3')
        doc = {'id': '1', 'source': 'product.txt', 'page': 0, 'chunk': 1,
               'score': .9, 'text': '演示基础售价为99元。'}
        result = {'answer': '演示基础售价为99元。', 'supported': True,
                  'citations': [doc], 'candidates': [doc], 'steps': ['测试检索流程']}
        store = MagicMock()
        store.count.return_value = 8
        service = MagicMock()
        service.ask.return_value = result
        with patch('config_data.get_settings', return_value=settings), \
                patch('vector_stores.VectorStore', return_value=store), \
                patch('rag.RAGService', return_value=service):
            app = AppTest.from_file(str(ROOT / 'app_qa.py'), default_timeout=30).run()
            self.assertEqual(len(app.exception), 0)
            price_button = next(x for x in app.button if x.label == '价格与优惠')
            price_button.click().run()
            self.assertEqual(len(app.exception), 0)
            service.ask.assert_called_once_with('云朵纯棉短袖T恤多少钱，新客有优惠吗？')
            self.assertIn('查看回答参考', [x.label for x in app.expander])
            self.assertFalse(any('RAG 流程' in x.label for x in app.expander))
            from file_history_store import HistoryStore
            history = HistoryStore(settings.history_db)
            session_id = history.sessions()[0]['id']
            self.assertEqual(len(history.messages(session_id)), 2)
            app.sidebar.toggle[0].set_value(True).run()
            self.assertTrue(any('RAG 流程' in x.label for x in app.expander))
            app.sidebar.toggle[0].set_value(False).run()
            service.ask.side_effect = RuntimeError('private diagnostic must not appear')
            next(x for x in app.button if x.label == '洗涤与养护').click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(history.messages(session_id)), 2)
            self.assertIn('暂时无法完成咨询', app.error[0].value)
            self.assertNotIn('private diagnostic', app.error[0].value)


if __name__ == '__main__':
    unittest.main()
