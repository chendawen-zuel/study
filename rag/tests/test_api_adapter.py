"""HTTP层兼容测试：本地测试服务器代替付费服务，使用产品的真实API客户端。

验证/embeddings和/chat/completions请求格式，不等于外部服务商已验收。
"""
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from langchain_core.documents import Document
from config_data import Settings, ROOT
from knowledge_base import import_file
from vector_stores import VectorStore
from rag import RAGService


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.paths.append(self.path)
        if self.path == '/v1/embeddings':
            inputs = body['input']
            if isinstance(inputs, str):
                inputs = [inputs]
            self.server.embedding_batches.append((len(inputs), body.get('encoding_format')))
            if len(inputs) > 10 or body.get('encoding_format') != 'float':
                self.send_error(400, 'Batch limit 10; float vectors required')
                return
            response = {'object': 'list', 'model': body['model'],
                        'data': [{'object': 'embedding', 'index': i, 'embedding': [1.0, 0.0, 0.0]}
                                 for i in range(len(inputs))],
                        'usage': {'prompt_tokens': 10, 'total_tokens': 10}}
        elif self.path == '/v1/chat/completions':
            self.server.chat_count += 1
            content = {'supported': True} if self.server.chat_count == 1 else {
                'answerable': True, 'answer': '本款不能高温烘干。', 'citation_ids': ['1']}
            response = {'id': 'chat-test', 'object': 'chat.completion', 'created': 1,
                        'model': body['model'], 'choices': [{
                            'index': 0, 'message': {'role': 'assistant', 'content': json.dumps(content)},
                            'finish_reason': 'stop'}],
                        'usage': {'prompt_tokens': 10, 'completion_tokens': 10, 'total_tokens': 20}}
        else:
            self.send_error(404)
            return
        payload = json.dumps(response).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class APIAdapterTests(unittest.TestCase):
    def test_real_clients_against_compatible_http(self):
        # 本地测试HTTP不能经过电脑的外部代理；只在测试期间覆盖。
        proxy_env = patch.dict(os.environ, {'NO_PROXY': '127.0.0.1,localhost', 'no_proxy': '127.0.0.1,localhost'})
        proxy_env.start()
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        server.paths, server.chat_count = [], 0
        server.embedding_batches = []
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            folder = ROOT / 'tmp' / 'tests'
            folder.mkdir(parents=True, exist_ok=True)
            temp = Path(tempfile.mkdtemp(dir=folder))
            url = f'http://127.0.0.1:{server.server_port}/v1'
            settings = Settings('test-only', url, 'test-chat', 'test-only', url, 'test-embedding',
                                data_dir=temp, chroma_dir=temp / 'chroma', history_db=temp / 'history.sqlite3')
            file = temp / '洗涤.txt'
            file.write_text('本款衣服不能高温烘干。', encoding='utf-8')
            store = VectorStore(settings)
            import_file(file, store)
            result = RAGService(settings, store).ask('衣服能烘干吗？')
            self.assertTrue(result['supported'])
            self.assertEqual(result['answer'], '本款不能高温烘干。')
            self.assertEqual(server.paths.count('/v1/embeddings'), 2)
            self.assertEqual(server.paths.count('/v1/chat/completions'), 2)
            # 大于10个片段的导入必须拆分，不能只验证小示例能用。
            docs = [Document(page_content=f'洗涤说明{i}', metadata={'source': '大文件.txt', 'chunk': i + 1})
                    for i in range(23)]
            store.replace_source('大文件.txt', docs)
            self.assertEqual(server.embedding_batches[-3:], [(10, 'float'), (10, 'float'), (3, 'float')])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
            proxy_env.stop()


if __name__ == '__main__':
    unittest.main()
