"""
使用示例 - Prompt Optimizer

运行前请确保:
1. 安装依赖: pip install anthropic
2. 设置环境变量: export ANTHROPIC_API_KEY="your-api-key"
"""

from prompt_optimizer import optimize_prompt, fill_prompt, pretty_print


def example_basic():
    """基本用法 - 让 Claude 自动选择变量"""
    print("=" * 60)
    print("示例 1: 基本用法")
    print("=" * 60)

    result = optimize_prompt("帮我写一封客户投诉回复邮件")

    print("\n提取的变量:", result["variables"])
    print("\n优化后的提示词模板:\n")
    print(pretty_print(result["prompt"]))


def example_with_variables():
    """指定变量的用法"""
    print("\n" + "=" * 60)
    print("示例 2: 指定变量")
    print("=" * 60)

    result = optimize_prompt(
        task="根据用户偏好从菜单中推荐菜品",
        variables=["MENU", "USER_PREFERENCES"]
    )

    print("\n提取的变量:", result["variables"])
    print("\n优化后的提示词模板:\n")
    print(pretty_print(result["prompt"]))


def example_fill_template():
    """填充模板的用法"""
    print("\n" + "=" * 60)
    print("示例 3: 填充模板变量")
    print("=" * 60)

    # 假设这是之前生成的模板
    template = """你将帮助用户从菜单中选择菜品。

<menu>
{$MENU}
</menu>

<user_preferences>
{$USER_PREFERENCES}
</user_preferences>

请根据用户偏好推荐最合适的菜品。"""

    filled = fill_prompt(
        template,
        MENU="1. 宫保鸡丁 - 微辣\n2. 清蒸鱼 - 清淡\n3. 麻婆豆腐 - 重辣",
        USER_PREFERENCES="不吃辣，喜欢清淡口味"
    )

    print("\n填充后的提示词:\n")
    print(filled)


if __name__ == "__main__":
    # 运行示例（需要有效的 API key）
    import os

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("警告: 未设置 ANTHROPIC_API_KEY 环境变量")
        print("请运行: export ANTHROPIC_API_KEY='your-api-key'")
        print("\n以下是模板填充示例（不需要 API key）:\n")
        example_fill_template()
    else:
        example_basic()
        example_with_variables()
        example_fill_template()
