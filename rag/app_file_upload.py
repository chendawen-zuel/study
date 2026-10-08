"""知识库更新页面。可由主页面打开，也可以单独用Streamlit启动。"""
import streamlit as st
from config_data import get_settings
from vector_stores import VectorStore
from knowledge_base import import_samples, import_file, save_upload


def render(settings):
    st.title('知识库管理')
    st.caption('导入 → 切块 → 调用向量 API → 存入本地 Chroma')
    st.info('上传内容会发送至你配置的向量服务商。请使用适合演示的公开资料。')
    st.write('内置资料：faq.txt（常见问题）、service.txt（售后与转人工）。')
    st.write('支持 TXT、Markdown、文字型 PDF，单文件最多10MB。修改同名文件后再次导入会更新对应片段。')
    if st.button('导入／更新内置服装客服资料', type='primary'):
        try:
            with st.spinner('正在生成向量并写入数据库…'):
                store = VectorStore(settings)
                result = import_samples(settings, store)
            st.success(f'导入完成：{sum(result.values())}个片段。')
            st.json(result)
        except Exception:
            st.error('导入失败：请检查 .env、向量模型、网络或API额度。原始资料已保留，可重试。')
    files = st.file_uploader('上传你的知识文件', type=['txt', 'md', 'pdf'], accept_multiple_files=True)
    if st.button('保存并导入上传文件', disabled=not files):
        try:
            store = VectorStore(settings)
        except Exception:
            st.error('向量服务初始化失败，请检查 .env 配置。')
            return
        for file in files:
            try:
                with st.spinner(f'正在导入 {file.name}…'):
                    path = save_upload(file.name, file.getvalue(), settings)
                    count = import_file(path, store)
                st.success(f'{file.name}：已导入{count}个片段。')
            except ValueError as e:
                st.error(str(e))
            except Exception:
                st.error(f'{file.name} 导入失败，请检查文件格式、网络或API配置，再次导入重试。')
    try:
        st.metric('当前模型对应的知识片段数', VectorStore(settings).count())
    except Exception:
        st.caption('填写有效API配置后可查看向量库状态。')


if __name__ == '__main__':
    st.set_page_config(page_title='知识库管理', page_icon='📚', layout='wide')
    render(get_settings())
