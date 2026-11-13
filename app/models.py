
"""Model adapters. The orchestrator talks to the ModelClient interface, not to a vendor SDK."""

from dataclasses import dataclass, field
from typing import Any, Protocol
import json


@dataclass
class ToolCall:
    name: str
    args: Any


@dataclass
class ModelTurn:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: Any = None


class ModelClient(Protocol):
    def generate(self, system: str, history: list[dict], tools: list[dict]) -> ModelTurn: ...


class ScriptedModelClient:
    """Deterministic stand-in for the LLM, used for the offline demo and automated tests."""

    def __init__(self, script: list):
        self._script = list(script)

    def generate(self, system, history, tools) -> ModelTurn:
        if not self._script:
            return ModelTurn(text="(script exhausted)")
        step = self._script.pop(0)
        return step(history) if callable(step) else step


# ============================================================
# GEMINI MODEL CLIENT (KEPT FOR FUTURE USE)
# ============================================================

# class GeminiModelClient:
#     """Gemini function calling. Automatic function calling is DISABLED."""
#
#     def __init__(self, model: str, api_key: str):
#         from google import genai
#         self._genai, self._model = genai, model
#         self._client = genai.Client(api_key=api_key)
#
#     def generate(self, system: str, history: list[dict], tools: list[dict]) -> ModelTurn:
#         from google.genai import types
#
#         declarations = [
#             types.FunctionDeclaration(
#                 name=t["name"],
#                 description=t["description"],
#                 parameters_json_schema=t["input_schema"]
#             )
#             for t in tools
#         ]
#
#         config = types.GenerateContentConfig(
#             system_instruction=system,
#             tools=[types.Tool(function_declarations=declarations)],
#             automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
#         )
#
#         response = self._client.models.generate_content(
#             model=self._model,
#             contents=self._to_contents(history, types),
#             config=config
#         )
#
#         calls = [
#             ToolCall(fc.name, dict(fc.args or {}))
#             for fc in (response.function_calls or [])
#         ]
#
#         text = "" if calls else (response.text or "")
#
#         return ModelTurn(
#             text=text,
#             tool_calls=calls,
#             raw=response.candidates[0].content
#         )
#
#     @staticmethod
#     def _to_contents(history: list[dict], types) -> list:
#         contents = []
#         for m in history:
#             if m["role"] == "user":
#                 contents.append(
#                     types.Content(
#                         role="user",
#                         parts=[types.Part.from_text(text=m["text"])]
#                     )
#                 )
#             elif m["role"] == "model":
#                 contents.append(
#                     m["raw"] if m.get("raw") is not None
#                     else types.Content(
#                         role="model",
#                         parts=[types.Part.from_text(text=m["text"])]
#                     )
#                 )
#             elif m["role"] == "tool":
#                 parts = [
#                     types.Part.from_function_response(
#                         name=r["name"],
#                         response=r["response"]
#                     )
#                     for r in m["results"]
#                 ]
#                 contents.append(types.Content(role="user", parts=parts))
#
#         return contents


# ============================================================
# GROQ MODEL CLIENT (ACTIVE)
# ============================================================

class GroqModelClient:
    """Groq function calling using LangChain.
    Tool execution remains under the control of the CampusConnect executor.
    """

    def __init__(self, model: str, api_key: str):
        from langchain_groq import ChatGroq

        self._model = ChatGroq(
            model=model,
            api_key=api_key,
            temperature=0
        )

    def generate(self, system: str, history: list[dict], tools: list[dict]) -> ModelTurn:
        from langchain_core.messages import (
            SystemMessage,
            HumanMessage,
            AIMessage,
            ToolMessage,
            FunctionMessage,
            BaseMessage,
        )

        messages = [SystemMessage(content=system)]

        # Keep track of tool-call IDs so that tool responses
        # are associated with the correct model requests.
        pending_ids = {}

        for m in history:

            if m["role"] == "user":
                messages.append(
                    HumanMessage(content=m["text"])
                )

            elif m["role"] == "model":
                raw = m.get("raw")

                if isinstance(raw, BaseMessage):
                    messages.append(raw)

                    for call in getattr(raw, "tool_calls", []):
                        pending_ids.setdefault(call["name"], []).append(
                            call["id"]
                        )

                else:
                    messages.append(
                        AIMessage(content=m.get("text", ""))
                    )

            elif m["role"] == "tool":
                for result in m["results"]:
                    name = result["name"]
                    response = result["response"]

                    content = (
                        response if isinstance(response, str)
                        else json.dumps(response, default=str)
                    )

                    ids = pending_ids.get(name, [])

                    if ids:
                        messages.append(
                            ToolMessage(
                                content=content,
                                tool_call_id=ids.pop(0)
                            )
                        )
                    else:
                        messages.append(
                            FunctionMessage(
                                name=name,
                                content=content
                            )
                        )

        # Convert CampusConnect tool definitions into
        # the format expected by LangChain.
        tool_definitions = [
            {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"]
            }
            for t in tools
        ]

        model_with_tools = self._model.bind_tools(tool_definitions)

        response = model_with_tools.invoke(messages)

        calls = [
            ToolCall(
                name=call["name"],
                args=call["args"]
            )
            for call in response.tool_calls
        ]

        text = "" if calls else str(response.content or "")

        return ModelTurn(
            text=text,
            tool_calls=calls,
            raw=response
        )
