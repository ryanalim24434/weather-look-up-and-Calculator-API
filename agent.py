import ast
import operator

import requests
from anthropic import Anthropic, beta_tool

client = Anthropic()

# Only these operators are allowed in the calculator — this whitelist is what
# keeps eval-style code injection out, since we never call Python's real eval().
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def safe_eval(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in SAFE_OPERATORS:
        return SAFE_OPERATORS[type(node.op)](safe_eval(node.left), safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in SAFE_OPERATORS:
        return SAFE_OPERATORS[type(node.op)](safe_eval(node.operand))
    raise ValueError("Unsupported expression")


@beta_tool
def calculator(expression: str) -> str:
    """Evaluate a basic math expression.

    Args:
        expression: A math expression using +, -, *, /, ** and parentheses, e.g. "17 * 0.4".
    """
    try:
        tree = ast.parse(expression, mode="eval")
        result = safe_eval(tree.body)
        return str(result)
    except Exception as e:
        return f"Error: could not evaluate '{expression}' ({e})"


@beta_tool
def get_weather(location: str) -> str:
    """Get the current weather for a city.

    Args:
        location: City name, e.g. "Chicago" or "Chicago, IL".
    """
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": location, "count": 1},
        timeout=10,
    ).json()

    if not geo.get("results"):
        return f"Could not find a location matching '{location}'."

    place = geo["results"][0]
    lat, lon = place["latitude"], place["longitude"]

    weather = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": lat, "longitude": lon, "current": "temperature_2m,weather_code"},
        timeout=10,
    ).json()

    current = weather["current"]
    temp_c = current["temperature_2m"]
    temp_f = temp_c * 9 / 5 + 32

    return f"{place['name']}: {temp_c}°C ({temp_f:.1f}°F)"


def main():
    messages = []
    print("Weather + Calculator agent. Type 'exit' to quit.\n")

    while True:
        user_input = input("you > ")
        if user_input.strip().lower() in ("exit", "quit"):
            break

        messages.append({"role": "user", "content": user_input})

        runner = client.beta.messages.tool_runner(
            model="claude-opus-4-8",
            max_tokens=1024,
            tools=[calculator, get_weather],
            messages=messages,
        )

        final_message = None
        for message in runner:
            final_message = message
            for block in message.content:
                if block.type == "tool_use":
                    print(f"  [calling tool: {block.name}({block.input})]")

        reply_text = "".join(
            block.text for block in final_message.content if block.type == "text"
        )
        print(f"claude > {reply_text}\n")
        messages.append({"role": "assistant", "content": final_message.content})


if __name__ == "__main__":
    main()
