"""
Prompt Optimizer - 基于 Anthropic Metaprompt 的提示词优化工具

使用方法:
    from prompt_optimizer import optimize_prompt

    # 基本用法
    result = optimize_prompt("帮我写一封客户投诉回复邮件")

    # 指定变量
    result = optimize_prompt(
        task="帮我写一封客户投诉回复邮件",
        variables=["CUSTOMER_EMAIL", "COMPANY_NAME"]
    )

    # 使用结果
    print(result["prompt"])      # 优化后的提示词模板
    print(result["variables"])   # 提取的变量列表
"""

import re
import os
from pathlib import Path
from typing import Optional

import anthropic


# 获取 metaprompt.txt 的路径
METAPROMPT_PATH = Path(__file__).parent / "metaprompt.txt"


def load_metaprompt() -> str:
    """加载 metaprompt 模板"""
    with open(METAPROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def extract_between_tags(tag: str, string: str, strip: bool = False) -> list[str]:
    """从字符串中提取指定标签之间的内容"""
    ext_list = re.findall(f"<{tag}>(.+?)</{tag}>", string, re.DOTALL)
    if strip:
        ext_list = [e.strip() for e in ext_list]
    return ext_list


def remove_empty_tags(text: str) -> str:
    """移除空标签"""
    return re.sub(r"<(\w+)></\1>$", "", text)


def extract_prompt(metaprompt_response: str) -> str:
    """从 metaprompt 响应中提取生成的提示词"""
    between_tags = extract_between_tags("Instructions", metaprompt_response)[0]
    return remove_empty_tags(remove_empty_tags(between_tags).strip()).strip()


def extract_variables(prompt: str) -> set[str]:
    """从提示词中提取变量名"""
    pattern = r"\{\$([^}]+)\}"
    variables = re.findall(pattern, prompt)
    return set(variables)


def optimize_prompt(
    task: str,
    variables: Optional[list[str]] = None,
    api_key: Optional[str] = None,
    model: str = "claude-sonnet-4-5-20250514",
    max_tokens: int = 4096,
    temperature: float = 0,
) -> dict:
    """
    优化提示词

    Args:
        task: 任务描述，例如 "帮我写一封客户投诉回复邮件"
        variables: 可选，指定变量名列表，例如 ["CUSTOMER_EMAIL", "COMPANY_NAME"]
                  如果不指定，Claude 会自动选择合适的变量
        api_key: Anthropic API 密钥，如果不提供则从环境变量 ANTHROPIC_API_KEY 获取
        model: 使用的模型，默认 claude-sonnet-4-5-20250514
        max_tokens: 最大生成 token 数
        temperature: 温度参数

    Returns:
        dict: {
            "prompt": str,           # 优化后的提示词模板
            "variables": set[str],   # 变量列表
            "raw_response": str      # 原始响应（包含规划过程）
        }

    Example:
        >>> result = optimize_prompt("帮我写一封客户投诉回复邮件")
        >>> print(result["prompt"])
        >>> print(result["variables"])
    """
    # 初始化客户端
    if api_key:
        client = anthropic.Anthropic(api_key=api_key)
    else:
        client = anthropic.Anthropic()  # 使用环境变量

    # 加载 metaprompt
    metaprompt = load_metaprompt()

    # 构建变量字符串
    variable_string = ""
    if variables:
        for var in variables:
            variable_string += "\n{$" + var.upper() + "}"

    # 替换任务占位符
    prompt = metaprompt.replace("{{TASK}}", task)

    # 构建 assistant 前缀（prefill）
    assistant_partial = "<Inputs>"
    if variable_string:
        assistant_partial += variable_string + "\n</Inputs><Instructions Structure>"

    # 调用 API
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": assistant_partial},
        ],
        temperature=temperature,
    )

    raw_response = message.content[0].text

    # 提取结果
    extracted_prompt = extract_prompt(assistant_partial + raw_response)
    extracted_variables = extract_variables(extracted_prompt)

    return {
        "prompt": extracted_prompt,
        "variables": extracted_variables,
        "raw_response": raw_response,
    }


def fill_prompt(prompt_template: str, **kwargs) -> str:
    """
    填充提示词模板中的变量

    Args:
        prompt_template: 提示词模板
        **kwargs: 变量名和值的键值对

    Returns:
        str: 填充后的提示词

    Example:
        >>> template = "Hello {$NAME}, welcome to {$COMPANY}!"
        >>> filled = fill_prompt(template, NAME="Alice", COMPANY="Anthropic")
        >>> print(filled)
        Hello Alice, welcome to Anthropic!
    """
    result = prompt_template
    for key, value in kwargs.items():
        # 支持 {$VAR} 格式
        result = result.replace("{$" + key.upper() + "}", str(value))
        result = result.replace("{$" + key + "}", str(value))
    return result


def pretty_print(message: str) -> str:
    """格式化输出文本"""
    return "\n\n".join(
        "\n".join(
            line.strip() for line in re.findall(r".{1,100}(?:\s+|$)", paragraph.strip("\n"))
        )
        for paragraph in re.split(r"\n\n+", message)
    )


# 命令行接口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Prompt Optimizer - 优化你的提示词")
    parser.add_argument("task", help="任务描述")
    parser.add_argument(
        "-v", "--variables",
        nargs="*",
        help="指定变量名（可选）",
        default=None
    )
    parser.add_argument(
        "-m", "--model",
        default="claude-sonnet-4-5-20250514",
        help="使用的模型"
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="显示原始响应"
    )

    args = parser.parse_args()

    print("正在优化提示词...")
    print("-" * 50)

    result = optimize_prompt(
        task=args.task,
        variables=args.variables,
        model=args.model,
    )

    print("\n变量:")
    print(result["variables"])
    print("\n" + "=" * 50)
    print("\n优化后的提示词:\n")
    print(pretty_print(result["prompt"]))

    if args.raw:
        print("\n" + "=" * 50)
        print("\n原始响应:\n")
        print(pretty_print(result["raw_response"]))
