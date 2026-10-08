"""服装购物咨询前端：消费者问答、咨询记录，以及折叠的商家管理入口。"""
import streamlit as st
from config_data import get_settings
from file_history_store import HistoryStore
from vector_stores import VectorStore
from rag import RAGService
from app_file_upload import render as render_upload
from ui_components import apply_styles, render_welcome, render_quick_questions


def show_result(result, technical=False):
    # 消费者只看到实际引用的资料；教学模式才展示候选片段和相似度。
    sources = {'product.txt': '商品介绍', 'faq.txt': '常见问题', 'service.txt': '售后服务'}
    citations = result.get('citations', [])
    if citations:
        with st.expander('查看回答参考'):
            for doc in citations:
                st.markdown(f'**{sources.get(doc["source"], "店铺资料")}**')
                st.text(doc['text'])
    if not technical:
        return
    with st.expander('学习演示：查看 RAG 流程与检索依据'):
        for step in result.get('steps', []):
            st.write(step)
        cited = {x['id'] for x in result.get('citations', [])}
        for doc in result.get('candidates', []):
            location = f'第{doc["page"]}页' if doc['page'] else f'片段{doc["chunk"]}'
            label = '已引用' if doc['id'] in cited else '候选'
            st.markdown(f'**[{doc["id"]}] {doc["source"]} · {location} · {label}**')
            st.caption(f'余弦相似度：{doc["score"]:.3f}，不是答案正确概率')
            st.text(doc['text'])


def main():
    st.set_page_config(page_title='云朵衣橱 · 购物咨询', page_icon='👕', layout='wide')
    apply_styles()
    settings = get_settings()
    history = HistoryStore(settings.history_db)
    with st.sidebar:
        st.title('云朵衣橱')
        st.caption('让日常穿搭，更简单一点。')
        with st.expander('商品数据更新与咨询'):
            # 这是本地演示的管理入口，不提供登录或权限控制。
            page = st.radio('页面', ['购物咨询', '知识库管理'])
            technical = st.toggle('展示学习演示信息', value=False)
            st.caption('本地演示管理入口；公开部署前需另行添加商家登录。')
        st.divider()
        if st.button('＋ 开始新的咨询', use_container_width=True):
            st.session_state.session_id = history.new_session()
        if not history.sessions():
            st.session_state.session_id = history.new_session()
        sessions = history.sessions()
        ids = [x['id'] for x in sessions]
        titles = {x['id']: x['title'] for x in sessions}
        current = st.session_state.get('session_id', ids[0])
        if current not in ids:
            current = ids[0]
        session_id = st.selectbox('我的咨询记录', ids, index=ids.index(current), format_func=lambda x: titles[x])
        st.session_state.session_id = session_id
        st.caption('每次提问请带上商品名称和关键信息，方便准确回答。')
        with st.expander('需要人工帮助？'):
            st.write('涉及订单查询、退款办理或投诉处理，请联系店铺人工客服。')
            st.caption('当前页面为演示，暂未接入真实人工客服。')
    if page == '知识库管理':
        render_upload(settings)
        return
    render_welcome()
    store, count = None, 0
    try:
        settings.validate()
    except ValueError as e:
        st.warning('咨询服务暂未就绪，请稍后再试。')
        if technical:
            st.info(str(e))
            st.code('复制 .env.example 为 .env，填写后重新启动页面。')
    else:
        try:
            store = VectorStore(settings)
            count = store.count()
        except Exception:
            st.error('咨询服务暂时不可用，请稍后再试。')
            if technical:
                st.info('向量库初始化失败，请检查依赖、路径与API配置。')
        if store is not None and count == 0:
            st.info('店铺咨询资料正在准备中，请稍后再来。')
            if technical:
                st.caption('请进入“商家与演示设置 → 知识库管理”，导入资料。')
    if technical and store is not None:
        st.caption(f'已入库 {count} 个片段 · 每个问题独立检索。')
    ready = store is not None and count > 0
    quick_question = render_quick_questions(disabled=not ready)
    st.divider()
    st.subheader('你的专属咨询')
    st.caption('尺码、优惠、洗护或售后，都可以在这里提问。')
    messages = history.messages(session_id)
    if not messages:
        with st.chat_message('assistant', avatar='👕'):
            st.write('你好，欢迎来到云朵衣橱！想了解哪件衣服？你可以点选上面的常见问题，也可以直接告诉我你的需求。')
    for message in messages:
        with st.chat_message(message['role'], avatar='👕' if message['role'] == 'assistant' else None):
            st.markdown(message['content'])
            if message['role'] == 'assistant':
                show_result(message['details'], technical=technical)
    st.caption('服装客服演示 · 商品和服务规则为示例，请以真实店铺信息为准。')
    typed_question = st.chat_input('输入商品或问题，例如：云朵T恤怎么选尺码？', max_chars=2000, disabled=not ready)
    question = typed_question or quick_question
    if question:
        with st.chat_message('user'):
            st.write(question)
        try:
            with st.spinner('正在查找适合你的回答…'):
                result = RAGService(settings, store).ask(question)
            history.save_turn(session_id, question, result)
            st.rerun()
        except Exception:
            # 不把API异常伪装成“知识库没有答案”，也不展示可能含密钥的原始报错。
            st.error('暂时无法完成咨询，请稍后重试，或联系店铺人工客服。')
            if technical:
                st.info('请检查网络、模型名称、密钥、API额度或JSON兼容性。此次未保存回答。')


if __name__ == '__main__':
    main()
