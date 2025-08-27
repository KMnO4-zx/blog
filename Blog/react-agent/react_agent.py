import json
import re
from typing import Dict, Any

class ReActAgent:
    def __init__(self, tools: Dict[str, callable], system_prompt: str):
        self.tools = tools
        self.system_prompt = system_prompt
        self.history = []
    
    def think(self, query: str) -> str:
        """思考下一步行动"""
        prompt = f"""{self.system_prompt}

当前问题：{query}
可用工具：{list(self.tools.keys())}
历史记录：{self.history}

请用以下格式回复：
Thought: 你的思考过程
Action: 工具名称
Action Input: 工具输入参数

如果不需要使用工具，直接回答即可。"""
        return prompt
    
    def parse_response(self, response: str) -> Dict[str, str]:
        """解析 LLM 响应"""
        lines = response.strip().split('\n')
        result = {'thought': '', 'action': None, 'action_input': None, 'final_answer': None}
        
        for line in lines:
            line = line.strip()
            if line.startswith('Thought:'):
                result['thought'] = line[8:].strip()
            elif line.startswith('Action:'):
                result['action'] = line[7:].strip()
            elif line.startswith('Action Input:'):
                result['action_input'] = line[13:].strip()
            elif not any(line.startswith(prefix) for prefix in ['Thought:', 'Action:', 'Action Input:']):
                if line.strip():
                    result['final_answer'] = line.strip()
        
        return result
    
    def act(self, action: str, action_input: str) -> str:
        """执行行动"""
        if action in self.tools:
            try:
                params = json.loads(action_input) if action_input else {}
                result = self.tools[action](params)
                return str(result)
            except json.JSONDecodeError:
                return "参数格式错误，请使用 JSON 格式"
            except Exception as e:
                return f"工具执行错误：{str(e)}"
        return f"无效的工具：{action}"
    
    def get_llm_response(self, prompt: str) -> str:
        """模拟 LLM 响应（实际项目中替换为真实 API 调用）"""
        # 这里是一个简单的模拟，实际项目中应该调用 OpenAI API
        if "计算" in prompt or "等于多少" in prompt:
            return """Thought: 用户需要计算数学表达式
Action: calculate
Action Input: {"expression": "15*3"}"""
        elif "天气" in prompt:
            return """Thought: 用户询问天气，需要查询天气信息
Action: weather
Action Input: {"city": "北京"}"""
        else:
            return "Thought: 这是一个简单的问题，可以直接回答\n这是一个模拟回答"
    
    def run(self, query: str, max_steps: int = 3) -> str:
        """运行 Agent 主循环"""
        self.history = []
        
        for step in range(max_steps):
            # 思考阶段
            thought_prompt = self.think(query)
            llm_response = self.get_llm_response(thought_prompt)
            parsed = self.parse_response(llm_response)
            
            if parsed['final_answer'] and not parsed['action']:
                return parsed['final_answer']
            
            if not parsed['action']:
                return f"步骤 {step + 1}：无法确定下一步行动"
            
            # 行动阶段
            observation = self.act(parsed['action'], parsed['action_input'])
            
            # 记录历史
            step_record = {
                'step': step + 1,
                'thought': parsed['thought'],
                'action': parsed['action'],
                'action_input': parsed['action_input'],
                'observation': observation
            }
            self.history.append(step_record)
            
            # 如果观察结果看起来像是最终答案，直接返回
            if "错误" not in observation and len(observation) > 0:
                return observation
        
        return f"达到最大步骤限制 ({max_steps}步)，当前结果：{self.history[-1]['observation'] if self.history else '无结果'}"

# 使用示例和测试
if __name__ == "__main__":
    # 定义工具函数
    def calculate_tool(params):
        """数学计算工具"""
        try:
            expression = params.get('expression', '')
            # 安全地计算表达式
            result = eval(expression, {"__builtins__": {}}, {})
            return f"计算结果：{expression} = {result}"
        except Exception as e:
            return f"计算错误：{str(e)}"
    
    def weather_tool(params):
        """天气查询工具（模拟）"""
        city = params.get('city', '未知城市')
        return f"{city}天气：晴天，25°C，微风"
    
    def search_tool(params):
        """搜索工具（模拟）"""
        query = params.get('query', '')
        return f"搜索'{query}'的结果：找到了相关信息"
    
    # 创建工具映射
    tools = {
        'calculate': calculate_tool,
        'weather': weather_tool,
        'search': search_tool
    }
    
    # 创建 Agent
    agent = ReActAgent(
        tools=tools,
        system_prompt="你是一个有帮助的 AI 助手，可以使用工具来回答问题。请仔细思考每一步。"
    )
    
    # 测试用例
    test_queries = [
        "计算 15*3 等于多少",
        "北京天气如何？",
        "搜索人工智能最新发展",
        "你好"
    ]
    
    print("=== ReAct Agent 测试 ===")
    for query in test_queries:
        print(f"\n问题：{query}")
        result = agent.run(query)
        print(f"结果：{result}")
        print("-" * 50)