# Agent 原理与最简实践

## 第一部分：Agent 原理深度解析

### Agent 核心概念

Agent（智能体）是能够感知环境、做出决策并采取行动以实现特定目标的自主实体。与传统程序相比，Agent 具备以下核心特征：

- **自主性**：无需人工干预即可独立运行
- **反应性**：能对环境变化做出实时响应
- **主动性**：主动追求目标而非被动响应
- **社会性**：能与其他 Agent 或人类进行交互

### ReAct 架构详解

ReAct（Reasoning + Acting）是目前最简洁有效的 Agent 架构，其核心思想是：

```
观察环境 → 思考推理 → 采取行动 → 观察结果 → 循环
```

**ReAct 决策循环**：
1. **Thought**：基于当前观察进行推理
2. **Action**：选择并执行具体行动
3. **Observation**：观察行动结果
4. **循环**：根据新观察继续思考

```mermaid
graph TD
    A[用户输入] --> B[Thought: 思考推理]
    B --> C{需要工具?}
    C -->|是| D[Action: 选择工具]
    C -->|否| E[直接回复]
    D --> F[执行工具调用]
    F --> G[Observation: 观察结果]
    G --> B
    E --> H[返回结果给用户]
    B --> H
    
    style A fill:#e1f5fe
    style H fill:#c8e6c9
    style B fill:#fff3e0
    style D fill:#fce4ec
    style G fill:#f3e5f5
```

**示例流程**：
```
用户："北京天气如何？"
Thought：用户询问天气，需要获取北京当前天气信息
Action：weather_query(location="北京")
Observation：{"temperature": 25, "condition": "晴"}
Thought：已获得天气数据，可以回复用户
Action：回复"北京今天25度，晴天"
```

### 其他主流 Agent 架构

**LangChain Agent**：
- 基于链式调用的 Agent 框架
- 支持多种提示模板
- 丰富的工具集成生态
- 适合复杂工作流

**AutoGPT**：
- 完全自主的目标追求
- 长期记忆系统
- 自我提示生成
- 适合开放式任务

**MetaGPT**:
- 软件开发的 Multi-Agent 协作框架
- 模拟真实软件团队角色分工
- 产品经理、架构师、工程师等角色扮演
- 适合自动化软件开发任务

**CAMELAI**:
- 基于角色扮演的对话式 Agent 框架
- 多 Agent 协作完成复杂任务
- 强调角色定义和通信协议
- 适合创意写作、教育培训等场景

**架构对比**：

| 架构 | 复杂度 | 控制力 | 适用场景 |
|------|--------|--------|----------|
| ReAct | 低 | 高 | 简单决策任务 |
| Swarm | 中 | 高 | 多 Agent 协作 |
| LangChain | 高 | 中 | 复杂工作流 |
| AutoGPT | 高 | 低 | 自主探索任务 |
| MetaGPT | 高 | 中 | 软件开发自动化 |
| CAMELAI | 中 | 高 | 角色扮演对话任务 |


## 第二部分：从零实现最简 React Agent

接下来会带领大家，手把手一步一步实现一个最简化的 React Agent。

**Agent 内部数据流**：

```mermaid
sequenceDiagram
    participant User
    participant Agent
    participant LLM
    participant Tools
    
    User->>Agent: 输入查询
    Agent->>Agent: 构建提示词
    Agent->>LLM: 发送提示
    LLM->>Agent: 返回思考+行动
    
    React 需要工具
        Agent->>Tools: 调用指定工具
        Tools->>Agent: 返回执行结果
        Agent->>Agent: 更新历史记录
        Agent->>LLM: 再次思考
        LLM->>Agent: 返回最终答案
    else 无需工具
        Agent->>User: 直接返回答案
    end
    
    Agent->>User: 最终结果
```

### Step 1: 构造大模型

首先我们需要一个大模型，这里我们使用 Qwen3-30B-A3B-Instruct-2507 的作为我们的 Agent 模型。Qwen3-30B-A3B-Instruct-2507 模型的工具调用能力非常强大，能够处理复杂的任务。

首先，还是先创建一个BaseModel类，我们可以在这个类中定义一些基本的方法，比如chat方法，方便以后扩展使用其他模型。

```python
class BaseModel:
    def __init__(self, api_key: str = '') -> None:
        self.api_key = api_key

    def chat(self, prompt: str, history: List[Dict[str, str]], system_prompt: str = "") -> Tuple[str, List[Dict[str, str]]]:
        """
        基础聊天接口
        
        Args:
            prompt: 用户输入
            history: 对话历史
            system_prompt: 系统提示
            
        Returns:
            (模型响应, 更新后的对话历史)
        """
        pass
```

接着，我们创建一个 Siliconflow 类，这个类继承自 BaseModel 类，我们在这个类中实现 chat 方法。硅基流动平台提供了很多开源模型的 api 服务，可以很方便的调试和开发。

```python
class Siliconflow(BaseModel):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key, base_url="https://api.siliconflow.cn/v1")

    def chat(self, prompt: str, history: List[Dict[str, str]] = [], system_prompt: str = "") -> Tuple[str, List[Dict[str, str]]]:
        """
        与 Siliconflow API 进行聊天
        
        Args:
            prompt: 用户输入
            history: 对话历史
            system_prompt: 系统提示
            
        Returns:
            (模型响应, 更新后的对话历史)
        """
        # 构建消息列表
        messages = [
            {"role": "system", "content": system_prompt or "You are a helpful assistant."}
        ]
        
        # 添加历史消息
        if history:
            messages.extend(history)
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": prompt})

        # 调用 API
        response = self.client.chat.completions.create(
            model="Qwen/Qwen3-30B-A3B-Instruct-2507",
            messages=messages,
            temperature=0.6,
            max_tokens=2000,
        )

        model_response = response.choices[0].message.content
        
        # 更新对话历史
        updated_history = messages.copy()
        updated_history.append({"role": "assistant", "content": model_response})

        return model_response, updated_history
```

### Step 2: 构造工具

我们在 `tools.py` 文件中，构造一些工具，比如 Google 搜索。在这个文件中，构造一个 `Tools` 类。在这个类中，我们需要添加一些工具的描述信息和具体实现方式。

添加工具的描述信息，是为了在构造`system_prompt`的时候，让模型能够知道可以调用哪些工具，以及工具的描述信息和参数。

- 首先要在 `tools` 中添加工具的描述信息
- 然后在 `tools` 中添加工具的具体实现

> 使用Google搜索功能的话需要去`serper`官网申请一下`token`: https://serper.dev/dashboard， 然后在tools.py文件中填写你的key，这个key每人可以免费申请一个，且有2500次的免费调用额度，足够做实验用啦~

以下为省略代码，详细代码可以在 [code/tools.py](./code/tool.py) 中查看

```python
class ReactTools:
    """
    React Agent 工具类
    
    为 ReAct Agent 提供标准化的工具接口
    """
    
    def __init__(self) -> None:
        self.toolConfig = self._build_tool_config()
    
    def _build_tool_config(self) -> List[Dict[str, Any]]:
        """构建工具配置信息"""
        return [
            {
                'name_for_human': '谷歌搜索',
                'name_for_model': 'google_search',
                'description_for_model': '谷歌搜索是一个通用搜索引擎，可用于访问互联网、查询百科知识、了解时事新闻等。',
                'parameters': [
                    {
                        'name': 'search_query',
                        'description': '搜索关键词或短语',
                        'required': True,
                        'schema': {'type': 'string'},
                    }
                ],
            }
        ]

    def google_search(self, search_query: str) -> str:
        """执行谷歌搜索

        可在 https://serper.dev/dashboard 申请 api key

        Args:
            search_query: 搜索关键词
            
        Returns:
            格式化的搜索结果字符串
        """
        url = "https://google.serper.dev/search"

        payload = json.dumps({"q": search_query})
        headers = {
            'X-API-KEY': 'your serper api key',
            'Content-Type': 'application/json'
        }

        pass
    
    def get_available_tools(self) -> List[str]:
        pass

    def get_tool_description(self, tool_name: str) -> str:
        pass
```

### Step 3: 构造 React Agent

现在我们开始构造核心的 React Agent。React Agent 是整个系统的协调者，负责管理 LLM 调用、工具执行和状态维护。这一步是构建 Agent 最关键的部分，让我们一步一步来实现。

#### 3.1 核心组件设计

**为什么要这样设计？**

React Agent 的设计采用了经典的**分层架构**模式：
- **接口层**：对外暴露简单的 `run()` 方法
- **协调层**：管理思考-行动-观察的循环
- **解析层**：从模型输出中提取结构化信息
- **执行层**：调用具体工具完成任务

这种设计让代码结构清晰，易于维护和扩展。

**ReactAgent 类结构**：

```python
class ReactAgent:
    def __init__(self, api_key: str = '') -> None:
        """初始化 React Agent"""
        self.api_key = api_key
        self.tools = Tools()                    # 工具管理
        self.model = Siliconflow(api_key)      # LLM 客户端
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """构建 ReAct 系统提示"""
        # 组合工具描述和 ReAct 模式指导
        return prompt_template
    
    def _parse_action(self, text: str) -> tuple[str, dict]:
        """解析模型输出中的行动和参数"""
        # 使用正则表达式提取行动和参数
        action_pattern = r"行动[:：]\s*(\w+)"
        action_input_pattern = r"行动输入[:：]\s*({.*?}|[^\n]*)"
        return action, action_input_dict
    
    def _execute_action(self, action: str, action_input: dict) -> str:
        """执行指定的工具行动"""
        # 调用对应工具并返回结果
        
    def run(self, query: str, max_iterations: int = 3, verbose: bool = True) -> str:
        """运行 ReAct Agent 主循环"""
        # 实现思考-行动-观察循环
```

#### 3.2 系统提示构建

**为什么系统提示如此重要？**

系统提示是 React Agent 的"大脑"，它直接决定了 Agent 的行为模式。一个好的系统提示应该包含：

1. **时间信息**：让 Agent 知道当前时间，避免过时信息
2. **工具清单**：明确告诉 Agent 有哪些工具可用
3. **行为模式**：详细的 ReAct 流程指导
4. **输出格式**：规范化的思考-行动-观察格式

**构建思路**：

我们使用 f-string 动态生成系统提示，这样可以：
- 自动包含当前时间
- 动态加载可用工具列表
- 保持提示的时效性和准确性

**系统提示模板解析**：

```python
prompt = f"""现在时间是 {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}。
你是一位智能助手，可以使用以下工具来回答问题：

{tool_descriptions}

请遵循以下 ReAct 模式：

思考：分析问题和需要使用的工具
行动：选择工具 [google_search] 中的一个
行动输入：提供工具的参数
观察：工具返回的结果

你可以重复以上循环，直到获得足够的信息来回答问题。

最终答案：基于所有信息给出最终答案

开始！"""
```

**设计要点**：
- **中文提示**：更符合国内用户习惯
- **具体工具名**：明确告诉模型可用工具
- **循环指导**：说明可以多次使用工具
- **最终答案**：明确结束条件

```python
prompt = f"""现在时间是 {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}。
你是一位智能助手，可以使用以下工具来回答问题：

{tool_descriptions}

请遵循以下 ReAct 模式：

思考：分析问题和需要使用的工具
行动：选择工具 [google_search] 中的一个
行动输入：提供工具的参数
观察：工具返回的结果

你可以重复以上循环，直到获得足够的信息来回答问题。

最终答案：基于所有信息给出最终答案

开始！"""
```

#### 3.3 行动解析机制

**为什么解析这么复杂？**

在实际应用中，大模型的输出格式往往不够规范，可能出现：
- 中英文混合的冒号
- JSON格式不规范
- 参数缺失或格式错误
- 多余的空格或换行

因此我们需要一个**鲁棒的解析机制**。

**解析思路**：

1. **多层匹配**：先用正则提取，再用JSON解析
2. **容错设计**：解析失败时提供降级方案
3. **格式兼容**：支持JSON字符串和纯文本参数

**解析流程详解**：

```
模型输出：
思考：用户询问特朗普生日，需要搜索
行动：google_search
行动输入：{"search_query": "特朗普生日"}

解析步骤：
1. 正则提取行动 → google_search
2. 正则提取参数 → {"search_query": "特朗普生日"}
3. JSON解析 → {'search_query': '特朗普生日'}
4. 返回结构化数据 → ('google_search', {'search_query': '特朗普生日'})
```

**常见错误场景**：

- ❌ `行动输入：特朗普生日` → 自动转为 `{"search_query": "特朗普生日"}`
- ❌ `行动输入：{"search_query":"特朗普生日"` → 补全JSON格式
- ❌ `行动输入："特朗普生日"` → 去除多余引号

**代码实现**：

```python
def _parse_action(self, text: str, verbose: bool = False) -> tuple[str, dict]:
    """从文本中解析行动和行动输入"""
    # 更灵活的正则表达式模式
    action_pattern = r"行动[:：]\s*(\w+)"
    action_input_pattern = r"行动输入[:：]\s*({.*?}|\{.*?\}|[^\n]*)"
    
    action_match = re.search(action_pattern, text, re.IGNORECASE)
    action_input_match = re.search(action_input_pattern, text, re.DOTALL)
    
    action = action_match.group(1).strip() if action_match else ""
    action_input_str = action_input_match.group(1).strip() if action_input_match else ""
    
    # 清理和解析JSON
    action_input_dict = {}
    if action_input_str:
        try:
            action_input_str = action_input_str.strip()
            if action_input_str.startswith('{') and action_input_str.endswith('}'):
                action_input_dict = json5.loads(action_input_str)
            else:
                # 如果不是JSON格式，尝试解析为简单字符串参数
                action_input_dict = {"search_query": action_input_str.strip('"\'')}
        except Exception as e:
            action_input_dict = {"search_query": action_input_str.strip('"\'')}
    
    return action, action_input_dict
```

#### 3.4 ReAct 主循环

**什么是 ReAct 循环？**

ReAct 循环是 Agent 的"心跳"，它让 Agent 能够：
- **持续思考**：基于新信息不断调整策略
- **工具调用**：在需要时主动获取外部信息
- **结果整合**：将工具结果与已有知识结合

**循环的四个阶段**：

1. **思考阶段**（Thought）：模型分析问题，决定是否需要工具
2. **行动阶段**（Action）：选择合适的工具并提供参数
3. **观察阶段**（Observation）：执行工具并获取结果
4. **整合阶段**（Integration）：将新信息整合到上下文中

**为什么需要 max_iterations？**

- **防止无限循环**：避免模型陷入死循环
- **控制成本**：限制 API 调用次数
- **用户体验**：避免过长的响应时间

**状态管理的重要性**：

每次循环都需要：
- **保持上下文**：将观察结果加入对话历史
- **更新输入**：为下一轮循环准备新的提示
- **历史记录**：确保模型知道之前做了什么

**循环逻辑详解**：

```python
def run(self, query: str, max_iterations: int = 3, verbose: bool = True) -> str:
    conversation_history = []
    current_text = f"问题：{query}"
    
    for iteration in range(max_iterations):
        # 获取模型响应
        response, history = self.model.chat(current_text, conversation_history, self.system_prompt)
        
        # 解析行动
        action, action_input = self._parse_action(response, verbose=verbose)
        
        if not action or action == "最终答案":
            return self._format_response(response)
        
        # 执行行动
        observation = self._execute_action(action, action_input)
        
        # 更新上下文继续对话
        current_text = f"{response}\n观察结果:{observation}\n"
        conversation_history = history
    
    return self._format_response(response)
```

#### 3.5 完整使用示例

**环境准备**：

在开始之前，请确保：
1. 已安装必要的库：`pip install openai json5 requests`
2. 已获取 Siliconflow API key（注册后免费获取）
3. 已获取 Serper API key（注册后免费获取2500次调用）

**分步骤运行**：

**第一步：基础测试**
```python
# 测试工具是否正常工作
from tool import ReactTools

tools = ReactTools()
result = tools.google_search("Python最新版本")
print("工具测试：", result[:100] + "...")
```

**第二步：Agent初始化**
```python
# 初始化 React Agent
agent = ReactAgent(api_key="your_api_key")

# 测试简单查询（无需工具）
response = agent.run("你好，请自我介绍", max_iterations=1)
print("简单查询：", response)
```

**第三步：复杂查询**
```python
# 测试需要工具的查询
response = agent.run("美国最近一次阅兵的原因有哪些？", max_iterations=3, verbose=True)
print("\n" + "="*50)
print("最终答案：", response)
```

**调试技巧**：

1. **查看详细日志**：设置 `verbose=True` 查看完整流程
2. **减少迭代次数**：测试时使用 `max_iterations=1` 快速验证
3. **检查API响应**：确保网络连接和API key有效
4. **错误排查**：观察绿色输出中的每一步执行状态

**输出示例**：

```
[ReAct Agent] 开始处理问题: 美国最近一次阅兵的原因有哪些？
[ReAct Agent] 第 1 次思考...
[ReAct Agent] 模型响应:
思考：用户询问美国最近一次阅兵的原因，我需要搜索相关信息
行动：google_search
行动输入：{"search_query": "美国最近一次阅兵 原因 2025"}
[ReAct Agent] 执行行动: google_search | 参数: {'search_query': '美国最近一次阅兵 原因 2025'}
[ReAct Agent] 观察结果:
1. **美国最近一次阅兵...**
...
[ReAct Agent] 已获得最终答案
最终答案：美国最近一次阅兵的主要原因包括...
```

![agent-demo](./images/agent-demo.png)



