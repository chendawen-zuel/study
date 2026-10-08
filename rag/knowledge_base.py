"""知识库更新：读取TXT/Markdown/文字PDF，切块，然后生成真实向量。"""
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED = {'.txt', '.md', '.pdf'}


def parse_file(path):
    path = Path(path)
    if path.suffix.lower() not in ALLOWED:
        raise ValueError('仅支持 TXT、Markdown 和文字型 PDF。')
    if path.stat().st_size > MAX_FILE_SIZE:
        raise ValueError('单个文件不能超过10MB。')
    if path.suffix.lower() == '.pdf':
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise ValueError('暂不支持加密PDF。')
        docs = [Document(page_content=p.extract_text() or '', metadata={'source': path.name, 'page': i + 1})
                for i, p in enumerate(reader.pages)]
    else:
        # UTF-8最适合项目跨平台使用；也支持Windows常见的GB18030文本。
        raw = path.read_bytes()
        try:
            text = raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            text = raw.decode('gb18030')
        docs = [Document(page_content=text, metadata={'source': path.name, 'page': 0})]
    docs = [d for d in docs if d.page_content.strip()]
    if not docs:
        raise ValueError('没有可提取文字；扫描PDF需要先做OCR。')
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=80,
        separators=['\n\n', '\n', '。', '；', ' ', ''],
    )
    chunks = splitter.split_documents(docs)
    for i, chunk in enumerate(chunks):
        chunk.metadata['chunk'] = i + 1
    return chunks


def import_file(path, store):
    chunks = parse_file(path)
    return store.replace_source(Path(path).name, chunks)


def import_samples(settings, store):
    # 示例文件位于data根目录；上传文件放子目录，两者文件名不能重复。
    result = {}
    for path in sorted(settings.data_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in ALLOWED:
            result[path.name] = import_file(path, store)
    return result


def save_upload(name, content, settings):
    # 不允许上传文件名包含路径，防止写出项目目录。
    if '/' in name or '\\' in name or name.startswith('.'):
        raise ValueError('文件名不能包含路径或以点开头。')
    if Path(name).suffix.lower() not in ALLOWED or len(content) > MAX_FILE_SIZE:
        raise ValueError('请上传不超过10MB的TXT、Markdown或文字PDF。')
    if (settings.data_dir / name).exists():
        raise ValueError('该名称属于内置示例，请更换上传文件名。')
    folder = settings.data_dir / 'uploads'
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / name
    target.write_bytes(content)
    return target
