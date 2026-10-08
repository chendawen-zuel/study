"""LangChain + Chroma：存向量、存原文、查相似片段。数据持久化在本地。"""
import hashlib
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings


class VectorStore:
    def __init__(self, settings, embeddings=None):
        self.settings = settings
        # 更换向量模型/服务商时使用新集合，避免不同向量维度混用。
        fingerprint = hashlib.sha256(
            f'{settings.embedding_url}|{settings.embedding_model}'.encode()
        ).hexdigest()[:16]
        if embeddings is None:
            settings.validate()
            embeddings = OpenAIEmbeddings(
                api_key=settings.embedding_key, base_url=settings.embedding_url,
                model=settings.embedding_model, check_embedding_ctx_length=False,
                # 百炼text-embedding-v4每次最多10条文本，LangChain自动分批发送。
                chunk_size=settings.embedding_batch_size,
                # 显式使用浮点向量，提高不同OpenAI兼容服务商之间的兼容性。
                model_kwargs={'encoding_format': 'float'},
                request_timeout=45, max_retries=1,
            )
        self.db = Chroma(
            collection_name=f'rag_demo_{fingerprint}',
            embedding_function=embeddings,
            persist_directory=str(settings.chroma_dir),
            collection_metadata={'hnsw:space': 'cosine'},
        )

    def count(self):
        return len(self.db.get(include=[])['ids'])

    def replace_source(self, source, documents):
        old_ids = self.db.get(where={'source': source}, include=[])['ids']
        # ID与文件内容绑定。同一文件重复导入会upsert，不会制造重复片段。
        ids = [hashlib.sha256(f'{source}|{i}|{d.page_content}'.encode()).hexdigest()
               for i, d in enumerate(documents)]
        self.db.add_documents(documents, ids=ids)
        obsolete = list(set(old_ids) - set(ids))
        if obsolete:
            self.db.delete(ids=obsolete)
        return len(ids)

    def search(self, question):
        if self.count() == 0:
            return []
        # cosine距离越小越相似；这里转为1-distance便于界面解释。
        found = self.db.similarity_search_with_score(question, k=self.settings.top_k)
        return [{
            'id': str(i + 1), 'text': doc.page_content,
            'source': doc.metadata['source'], 'page': doc.metadata.get('page', 0),
            'chunk': doc.metadata['chunk'], 'score': round(1 - float(distance), 4),
        } for i, (doc, distance) in enumerate(found)]
