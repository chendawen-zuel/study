"""消费者页面的展示组件：只负责样式和静态介绍，不处理检索或支付。"""
import streamlit as st


def apply_styles():
    # 样式仅作用于展示元素；聊天、按钮和输入框继续使用Streamlit原生组件。
    st.markdown('''<style>
    .stApp {background: #faf8f4; color: #302b28;}
    [data-testid="stSidebar"] {background: #f0ece5;}
    .block-container {max-width: 1140px; padding-top: 2.4rem; padding-bottom: 2rem;}
    h1, h2, h3 {letter-spacing: -.025em;}
    [data-testid="stChatMessage"] {border: 1px solid #e8e1d8; border-radius: 18px; background: #fffdfa;}
    .cloud-hero {display: grid; grid-template-columns: 1.4fr 1fr; gap: 32px;
      align-items: center; padding: 38px; border: 1px solid #e4d9cd;
      border-radius: 26px; background: #f3ede4; margin-bottom: 28px;}
    .cloud-eyebrow {color: #9c573d; font-size: 12px; letter-spacing: .15em; font-weight: 700;}
    .cloud-heading {font-size: clamp(28px, 3.8vw, 44px); font-weight: 750;
      line-height: 1.3; margin: 18px 0 16px; color: #302b28;}
    .cloud-copy {font-size: 15px; color: #665d55; line-height: 1.9; max-width: 440px;}
    .cloud-tags {display: flex; flex-wrap: wrap; gap: 8px; margin-top: 22px;}
    .cloud-tag {font-size: 12px; border: 1px solid #d9cbbb; border-radius: 30px;
      padding: 6px 12px; color: #65584b; background: #ffffff66;}
    .cloud-product {padding: 20px 24px; border-radius: 20px; background: #fffaf2;
      border: 1px solid #e7ded1; text-align: center;}
    .cloud-product svg {width: 100%; max-width: 230px; height: 170px;}
    .cloud-product-name {font-weight: 650; font-size: 17px; margin: 12px 0 5px;}
    .cloud-product-note {color: #786c60; font-size: 12px; line-height: 1.8;}
    .cloud-section-label {color: #9c573d; font-size: 12px; font-weight: 700;
      letter-spacing: .08em; margin: 8px 0;}
    @media (max-width: 720px) {
      .cloud-hero {grid-template-columns: 1fr; padding: 24px; gap: 22px;}
      .cloud-product svg {height: 130px;}
      .block-container {padding-top: 1.4rem;}
    }
    </style>''', unsafe_allow_html=True)


def render_welcome():
    # 这里不插入用户输入，避免把聊天内容当成HTML执行。
    # 插图仅作服装示意；真实价格和售后答案来自知识库。
    st.markdown('''<div class="cloud-hero">
      <div>
        <div class="cloud-eyebrow">云朵衣橱 / 购物咨询</div>
        <h1 class="cloud-heading">选得合适，<br>穿得舒服。</h1>
        <div class="cloud-copy">从尺码、面料到洗护与售后，<br>
          把你关心的问题告诉我们，给日常穿搭多一点安心。</div>
        <div class="cloud-tags"><span class="cloud-tag">商品与尺码</span>
          <span class="cloud-tag">价格与优惠</span><span class="cloud-tag">洗护与售后</span></div>
      </div>
      <div class="cloud-product">
        <svg viewBox="0 0 260 190" role="img" aria-label="米白色圆领短袖示意图">
          <ellipse cx="130" cy="175" rx="80" ry="7" fill="#eae0d2"/>
          <path d="M91 22L62 32 22 76 58 103 76 84 76 163Q130 176 184 163L184 84 202 103 238 76 198 32 169 22Q130 46 91 22Z"
            fill="#f8f5ee" stroke="#b7a48d" stroke-width="2.5" stroke-linejoin="round"/>
          <path d="M91 22Q130 78 169 22M76 84L78 53M184 84L182 53M81 157Q130 167 179 157"
            fill="none" stroke="#d6c6b3" stroke-width="2"/>
        </svg>
        <div class="cloud-product-name">云朵纯棉短袖 T 恤</div>
        <div class="cloud-product-note">日常基础款 · 服装示意图<br>演示商品，详情以咨询资料为准</div>
      </div>
    </div>''', unsafe_allow_html=True)


def render_quick_questions(disabled=False):
    """点击常见问题即可发送咨询；仍然走真实RAG流程，不使用预设答案。"""
    st.markdown('<div class="cloud-section-label">从这里开始</div>', unsafe_allow_html=True)
    st.subheader('你想了解什么？')
    questions = [
        ('尺码怎么选', '云朵纯棉短袖T恤的尺码怎么选？'),
        ('颜色与面料', '云朵纯棉短袖T恤是什么面料，有哪些颜色？'),
        ('价格与优惠', '云朵纯棉短袖T恤多少钱，新客有优惠吗？'),
        ('洗涤与养护', '云朵纯棉短袖T恤如何清洗？'),
        ('退换与退款', '尺码不合适怎么退换，退款金额怎么算？'),
        ('投诉与人工', '遇到售后问题怎样投诉或转人工？'),
    ]
    chosen = None
    for row in range(2):
        columns = st.columns(3)
        for column, (label, question) in zip(columns, questions[row * 3:(row + 1) * 3]):
            if column.button(label, key=f'quick_{row}_{label}',
                             use_container_width=True, disabled=disabled):
                chosen = question
    return chosen
