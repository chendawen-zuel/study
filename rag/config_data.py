"""统一配置：所有本地文件都相对于本文件定位，避免启动目录不同导致串库。"""
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
# 只读取项目自己的 .env，不把配置复制到数据库或日志。
load_dotenv(ROOT / '.env')
FALLBACK = '知识库中暂时没有找到相关答案，建议转人工客服处理。'


@dataclass(frozen=True)
class Settings:
    api_key: str
    base_url: str
    chat_model: str
    embedding_key: str
    embedding_url: str
    embedding_model: str
    threshold: float = 0.55
    top_k: int = 4
    embedding_batch_size: int = 10
    data_dir: Path = ROOT / 'data'
    chroma_dir: Path = ROOT / 'chroma_db'
    history_db: Path = ROOT / 'chat_history' / 'history.sqlite3'

    def validate(self):
        if not self.api_key:
            raise ValueError('请在 .env 中填写 AI_API_KEY（聊天模型密钥）。')
        if not self.embedding_key:
            raise ValueError('请在 .env 中填写 EMBEDDING_API_KEY（百炼向量密钥）。')
        if not self.chat_model or not self.embedding_model:
            raise ValueError('聊天模型与向量模型名称不能为空。')
        if not -1 <= self.threshold <= 1 or not 1 <= self.top_k <= 20:
            raise ValueError('相似度阈值应在 -1 到 1 之间，TOP_K 应在 1 到 20 之间。')
        if not 1 <= self.embedding_batch_size <= 10:
            raise ValueError('向量API每批数量应在1到10之间，以兼容百炼text-embedding-v4。')


def is_bailian_url(url):
    """识别百炼共享域名和业务空间域名，用于判断能否沿用聊天密钥。"""
    host = urlparse(url).hostname or ''
    return host in {'dashscope.aliyuncs.com', 'dashscope-intl.aliyuncs.com',
                    'cn-hongkong.dashscope.aliyuncs.com'} or host.endswith('.maas.aliyuncs.com')


def get_settings():
    key = os.getenv('AI_API_KEY', '').strip()
    url = os.getenv('AI_BASE_URL', 'https://api.openai.com/v1').strip()
    embedding_url = os.getenv('EMBEDDING_BASE_URL', '').strip() or url
    embedding_key = os.getenv('EMBEDDING_API_KEY', '').strip()
    # 不把其他平台的聊天密钥误发给百炼。不同服务商必须显式配置向量密钥。
    same_service = embedding_url.rstrip('/') == url.rstrip('/')
    both_bailian = is_bailian_url(url) and is_bailian_url(embedding_url)
    if not embedding_key and (same_service or both_bailian):
        embedding_key = key
    return Settings(
        api_key=key, base_url=url,
        chat_model=os.getenv('AI_CHAT_MODEL', 'gpt-4o-mini').strip(),
        embedding_key=embedding_key,
        embedding_url=embedding_url,
        embedding_model=os.getenv('AI_EMBEDDING_MODEL', 'text-embedding-3-small').strip(),
        threshold=float(os.getenv('RETRIEVAL_THRESHOLD', '0.55')),
        top_k=int(os.getenv('RETRIEVAL_TOP_K', '4')),
        embedding_batch_size=int(os.getenv('EMBEDDING_BATCH_SIZE', '10')),
    )
