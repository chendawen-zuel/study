# 基础 RAG 知识演示项目

用户提问 → 查本地知识库 → 检查证据是否足够 → 依据证据回答，或转人工。

内置的是虚构服装店资料，便于理解截图中的尺码、养护、颜色场景。所有源码、配置、数据库和上传资料都位于本项目目录。聊天模型与向量模型均调用真实 OpenAI 兼容 API，不使用模拟模型运行产品。

GitHub版本包含源码、配置模板、测试及当前的 `faq.txt`、`service.txt`。当前本地 `data` 根目录没有 `product.txt`，商品资料可通过“知识库管理”自行上传，或添加为 `data/product.txt` 后导入。API密钥、虚拟环境、数据库、聊天记录、用户上传资料和大体积演示视频不随仓库发布。

## 1. 安装和启动（Windows PowerShell）

建议 Python 3.11 或 3.12。首次下载，在 PowerShell 中运行：

```powershell
git clone https://github.com/chendawen-zuel/study.git
cd study/rag
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

编辑 `.env`，保存后启动：

```powershell
.\.venv\Scripts\python.exe -m streamlit run app_qa.py --server.address 127.0.0.1
```

打开 http://localhost:8501 。不需要激活虚拟环境。已有 `.env` 时不要再次复制覆盖。

当前安装环境的完整版本已记录在 `requirements-lock.txt`；同为Windows和Python 3.12时，可用它替代 `requirements.txt` 安装以复现本次验证环境。

也可以双击 `启动演示.cmd`。知识库更新页面已集成在主页面左侧，不必启动第二个服务。如需单独演示上传程序：

```powershell
.\.venv\Scripts\python.exe -m streamlit run app_file_upload.py --server.address 127.0.0.1 --server.port 8502
```

## 2. 配置真实 API

至少填写以下内容：

| 配置 | 含义 |
| --- | --- |
| AI_API_KEY | 聊天服务商的密钥 |
| AI_BASE_URL | 兼容接口的基础地址，通常以 `/v1` 结尾 |
| AI_CHAT_MODEL | 服务商支持的聊天模型名称 |
| AI_EMBEDDING_MODEL | 服务商支持的向量模型名称 |
| EMBEDDING_API_KEY / EMBEDDING_BASE_URL | 百炼向量密钥与兼容接口地址；聊天可使用另一家服务商 |
| EMBEDDING_BATCH_SIZE | 每次发送的文本条数，默认10，兼容百炼v4限制 |

`.env.example` 中的模型名仅为示例，需更换成你的服务商实际支持的名称。只提供聊天接口的服务商不能生成向量，需要另外配置支持 `/embeddings` 的服务商。聊天接口需要支持标准 `/chat/completions`，模型应能够遵循JSON输出要求；不要求工具调用或JSON Schema接口。

不要在聊天中发送真实密钥，也不要上传 `.env`。修改配置后重启 Streamlit。更换向量模型或服务地址会切换到新的Chroma集合，需要重新导入资料。

### 阿里云百炼向量配置

聊天配置 `AI_API_KEY / AI_BASE_URL / AI_CHAT_MODEL` 保持你已有的设置。向量部分填写：

```dotenv
EMBEDDING_API_KEY=填写你的百炼密钥
EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
AI_EMBEDDING_MODEL=text-embedding-v4
EMBEDDING_BATCH_SIZE=10
```

示例地址是北京地域的共享地址；也可使用百炼控制台推荐的业务空间地址，密钥、地址和模型的地域与权限需要匹配。如果聊天和向量都来自百炼，可共用有效百炼密钥。其他平台的聊天密钥不会自动发给百炼，必须单独填写 `EMBEDDING_API_KEY`。

项目通过 `OpenAIEmbeddings` 调用百炼兼容接口，不需要安装LlamaIndex。请求显式使用 `encoding_format=float`；23个文档片段会按10、10、3分批发送。这里的批量条数与文档切块的字符数是不同参数。

参考：https://help.aliyun.com/zh/model-studio/embedding-interfaces-compatible-with-openai

## 3. 三分钟演示

1. 在左侧展开“商家与演示设置”，切换到“知识库管理”，点击“导入／更新内置服装客服资料”。这一步会调用真实向量API并产生费用。
2. 回到“购物咨询”，点击快捷问题或提问“这件T恤可以用高温烘干机吗？”，查看回答并展开“查看回答参考”。
3. 提问“有哪些颜色可以选择？”展示颜色资料的召回。
4. 提问“北京明天的天气怎样？”应返回：**知识库中暂时没有找到相关答案，建议转人工客服处理。**
5. 上传一份自己的TXT或文字PDF，重新提问，展示知识库如何更新。
6. 刷新页面或重启服务，历史对话仍保存在SQLite中。

使用UTF-8保存TXT最方便。上传同名文件会更新该来源的向量片段。导入失败后上传原文件重试即可；已经导入成功的文件不受其他文件失败影响。扫描PDF暂不做OCR。

首页面向服装消费者，提供尺码、面料、价格优惠、洗护、退换和投诉六个快捷入口。快捷问题仍调用真实RAG服务，并保存咨询记录。默认不显示API配置、相似度和检索步骤；在“商家与演示设置”开启“展示学习演示信息”即可查看。资料未就绪时会禁用提问入口，API调用失败会显示服务异常，不会伪装成无答案。

商家管理入口仅为本地演示导航，不提供身份验证。此项目的咨询记录保存在本机，未做多用户隔离；公开部署前需要添加商家权限和消费者会话隔离。示意图、商品及服务规则均为演示内容，页面不执行购买、退款或真实人工转接。

## 4. 按截图理解代码

| 文件 | 责任 |
| --- | --- |
| app_qa.py | 主前端：聊天、历史切换、流程和证据显示 |
| ui_components.py | 消费者页面样式、服装示意图及快捷咨询入口 |
| app_file_upload.py | 知识库更新前端：导入示例和上传文件 |
| config_data.py | 从项目 `.env` 读取服务商、模型、阈值、路径 |
| file_history_store.py | 用SQLite保存会话与问答，事务写入 |
| knowledge_base.py | 解析文档、保留页码、切块、导入 |
| vector_stores.py | LangChain封装Chroma，调用向量API与相似检索 |
| rag.py | LangGraph核心：检索、证据检查、生成、转人工 |
| data/product.txt | 服装介绍、适合人群、核心功能、尺码、价格与优惠活动 |
| data/faq.txt | 常见问题及标准回答，包含洗涤养护说明 |
| data/service.txt | 售后、退款、投诉与转人工规则 |
| tests/test_rag.py | 离线验证图分支、真实Chroma持久化与SQLite历史 |

运行后生成：

```text
rag/
├── data/uploads/          用户上传资料
├── chroma_db/             Chroma持久化向量、原文和元数据
├── chat_history/
│   └── history.sqlite3    SQLite关系数据库
└── .env                   本地API配置，不入Git
```

SQLite保存 `sessions` 和 `messages`。回答记录包含检索候选、引用和流程步骤。Chroma保存文档片段、向量以及来源、页码、片段编号。这是两个不同用途的存储。

## 5. 核心流程与边界

```text
START → retrieve → check_evidence ─ 有充分证据 → generate → END
                              └─ 无充分证据 → fallback → END
```

检索先取最多TOP_K个候选，以 `1 - cosine距离` 转成相似度，低于阈值的片段不用于回答。相似度不是正确概率；默认0.55只是演示起点，要用自己的命中题和无答案题调整。

通过阈值也不等于能回答：模型会再次检查证据是否足够，减少“只是主题相近却乱回答”的情况。回答必须附带有效的片段编号，页面把编号映射到本地真实出处。结构正确并不能保证语义完全正确，重要演示题仍需人工检查。

每个问题独立检索。历史用于持久保存和展示，不会自动作为事实证据或改写指代问题。“它呢？”等依赖前文的问题请补全商品或主题。

模型调用失败、配置错误、额度不足和模型返回非法JSON会提示处理失败，不会冒充知识库缺失答案。空知识库或无充分证据返回固定转人工文案；本项目只给出提示，没有对接真实人工客服。

单机本地教学演示没有账号、权限管理及多进程写入协调，建议只绑定127.0.0.1。用户上传的文本会送至向量服务商，召回的片段与问题会送至聊天服务商。

## 6. 测试与学习顺序

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

离线测试使用明确标记的测试替身，不调用付费API；其中Chroma、SQLite和LangGraph是真实运行。真实API验收需要你的有效配置：导入示例，验证命中、未命中和引用，再刷新检查历史。未配置密钥不能声称已经完成真实API端到端验证。

建议学习顺序：配置 → 文档解析 → 向量存储 → LangGraph流程 → SQLite → 前端。

### 本次验证结果（2026-10-08）

- 13项测试通过：命中并引用、无命中、空库、相关但证据不足、非法引用、更新去重、输入路径与JSON异常、API客户端HTTP兼容、前端导航和会话，以及配置隔离和批量限制。新增消费者快捷咨询、引用资料显示、技术信息开关及失败不保存回答的检查。HTTP测试验证23个片段按10、10、3分批发送。
- SQLite和Chroma持久化检查通过；依赖检查无冲突。
- 本地Streamlit服务健康检查返回 `ok`。
- 消费者页面已在本地启动。浏览器自动预览工具因运行环境初始化错误未能打开，尚未完成截图视觉检查；前端交互已通过Streamlit AppTest验证。
- 检测到本地配置中已有聊天和向量密钥，未输出密钥。真实向量服务验证在连接阶段返回 `APIConnectionError`，没有成功完成入库和问答；需检查地域接口地址、网络或代理后重试。不能据此确认密钥有效。HTTP兼容测试使用本地测试服务器，不代表真实外部服务已验收。

官方参考：
- https://docs.langchain.com/oss/python/integrations/vectorstores/chroma
- https://docs.langchain.com/oss/python/integrations/chat/openai
- https://docs.langchain.com/oss/python/langgraph/graph-api
