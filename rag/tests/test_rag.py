"""离线集成测试：替身只用于API层，真实运行Chroma、LangGraph与SQLite。"""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from langchain_core.embeddings import Embeddings
from config_data import Settings, FALLBACK, ROOT
from vector_stores import VectorStore
from knowledge_base import import_file, save_upload
from file_history_store import HistoryStore
from rag import RAGService


class TestEmbeddings(Embeddings):
    """确定性测试向量；产品不使用这个类。"""
    def embed_query(self, text):
        if '洗' in text or '烘干' in text:
            return [1.0, 0.0, 0.0]
        if '颜色' in text:
            return [0.0, 1.0, 0.0]
        return [0.0, 0.0, 1.0]

    def embed_documents(self, texts):
        return [self.embed_query(x) for x in texts]


class TestLLM:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1
        if not self.replies:
            raise AssertionError('不该调用额外的模型请求')
        return SimpleNamespace(content=self.replies.pop(0))


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        # Chroma会持有文件句柄，Windows测试运行时使用不同集合目录。
        test_root = ROOT / 'tmp' / 'tests'
        test_root.mkdir(parents=True, exist_ok=True)
        self.temp = Path(tempfile.mkdtemp(prefix='rag-test-', dir=test_root))
        self.settings = Settings('test', 'https://test.invalid/v1', 'test', 'test',
                                 'https://test.invalid/v1', 'test', data_dir=self.temp / 'data',
                                 chroma_dir=self.temp / 'chroma', history_db=self.temp / 'history.sqlite3')
        self.settings.data_dir.mkdir()
        self.path = self.settings.data_dir / '洗涤.txt'
        self.path.write_text('本款T恤洗涤使用30度水，不可高温烘干。', encoding='utf-8')
        self.store = VectorStore(self.settings, TestEmbeddings())
        import_file(self.path, self.store)

    def test_hit_citations_history_and_persistence(self):
        llm = TestLLM(['{"supported":true}', '{"answerable":true,"answer":"不可高温烘干。","citation_ids":["1"]}'])
        result = RAGService(self.settings, self.store, llm).ask('可以高温烘干吗？')
        self.assertTrue(result['supported'])
        self.assertEqual(result['citations'][0]['source'], '洗涤.txt')
        history = HistoryStore(self.settings.history_db)
        session = history.new_session()
        history.save_turn(session, '可以高温烘干吗？', result)
        self.assertEqual(len(HistoryStore(self.settings.history_db).messages(session)), 2)
        reopened = VectorStore(self.settings, TestEmbeddings())
        self.assertEqual(reopened.count(), 1)

    def test_miss_does_not_call_chat(self):
        llm = TestLLM([])
        result = RAGService(self.settings, self.store, llm).ask('明天天气怎样？')
        self.assertEqual(result['answer'], FALLBACK)
        self.assertEqual(llm.calls, 0)

    def test_empty_store_returns_fallback(self):
        self.store.db.delete(ids=self.store.db.get(include=[])['ids'])
        llm = TestLLM([])
        result = RAGService(self.settings, self.store, llm).ask('怎么洗？')
        self.assertEqual(result['answer'], FALLBACK)
        self.assertEqual(llm.calls, 0)

    def test_related_but_insufficient(self):
        llm = TestLLM(['{"supported":false}'])
        result = RAGService(self.settings, self.store, llm).ask('洗涤剂的品牌是什么？')
        self.assertEqual(result['answer'], FALLBACK)
        self.assertEqual(llm.calls, 1)

    def test_invalid_citation_fails_closed(self):
        llm = TestLLM(['{"supported":true}', '{"answerable":true,"answer":"编造答案","citation_ids":["99"]}'])
        result = RAGService(self.settings, self.store, llm).ask('怎么洗？')
        self.assertEqual(result['answer'], FALLBACK)

    def test_update_without_duplicates(self):
        import_file(self.path, self.store)
        self.assertEqual(self.store.count(), 1)
        self.path.write_text('本款T恤洗涤使用冷水，不要烘干。', encoding='utf-8')
        import_file(self.path, self.store)
        self.assertEqual(self.store.count(), 1)
        self.assertIn('冷水', self.store.search('怎么洗？')[0]['text'])

    def test_upload_path_validation_and_bad_json(self):
        with self.assertRaises(ValueError):
            save_upload('../escape.txt', b'x', self.settings)
        llm = TestLLM(['not json'])
        with self.assertRaises(ValueError):
            RAGService(self.settings, self.store, llm).ask('怎么洗？')


if __name__ == '__main__':
    unittest.main()
