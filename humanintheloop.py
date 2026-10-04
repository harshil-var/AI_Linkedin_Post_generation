import os 
import sys
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from dotenv import load_dotenv

# Ensure UTF-8 output encoding for Windows standard output
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def safe_print(text: str):
    """Safely print text without raising UnicodeEncodeError on Windows cp1252 consoles."""
    try:
        print(text)
    except UnicodeEncodeError:
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout.buffer.write((str(text) + '\n').encode('utf-8', errors='replace'))
            sys.stdout.buffer.flush()
        else:
            print(str(text).encode('ascii', errors='replace').decode('ascii'))


load_dotenv()

# tools
search_tool = TavilySearch(max_results=3)
tools = [search_tool]
tool_node = ToolNode(tools)

# llms 
writer_llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")
writer_llm_with_tools = writer_llm.bind_tools(tools)

# state building 
class State(TypedDict):
    topic: str 
    messages: Annotated[list, add_messages]
    draft: str 
    review_feedback: str
    is_approved: bool 
    attempt: int


WRITER_SYSTEM_PROMPT = (
    "You are an expert LinkedIn content writer. Write engaging, professional "
    "LinkedIn posts about the given topic. "
    "Rules: strong hook in the first line, one clear takeaway, easy to skim "
    "with short paragraphs, roughly 150-200 words, end with an engaging "
    "question or CTA, no hashtags. "
    "If you receive feedback on a previous draft, address every point carefully. "
    "If current real-world information or web data is needed, use the web search tool."
)


def writer_node(state: State) -> dict:
    """Writes (or rewrites) the LinkedIn post using writer LLM with Tavily tools."""
    attempt = state.get("attempt", 0)
    topic = state["topic"]
    previous_feedback = state.get("review_feedback", "")
    existing_messages = state.get("messages", [])

    safe_print(f"\n[Attempt {attempt + 1}] Writer is drafting the post...")

    # If returning from a tool call, pass full conversation history (SystemMessage + messages) to Gemini
    if existing_messages and getattr(existing_messages[-1], "type", None) == "tool":
        prompt_messages = [SystemMessage(content=WRITER_SYSTEM_PROMPT)] + list(existing_messages)
        response = writer_llm_with_tools.invoke(prompt_messages)
        return {
            "messages": [response]
        }

    if previous_feedback and previous_feedback != "Approved by human.":
        user_message_text = (
            f"Your previous draft on '{topic}' was rejected.\n\n"
            f"Reviewer feedback:\n{previous_feedback}\n\n"
            f"Write a NEW improved LinkedIn post that fixes every issue mentioned.\n"
            f"Use the web search tool if needed."
        )
    else:
        user_message_text = (
            f"Write a LinkedIn post on this topic: {topic}\n"
            f"If current information is necessary, use the web search tool."
        )

    human_msg = HumanMessage(content=user_message_text)
    system_msg = SystemMessage(content=WRITER_SYSTEM_PROMPT)

    response = writer_llm_with_tools.invoke([system_msg, human_msg])

    return {
        "messages": [human_msg, response]
    }


def extract_draft_node(state: State) -> dict:
    """Extract the final text response from the writer and track attempt."""
    attempt = state.get("attempt", 0) + 1

    for message in reversed(state["messages"]):
        if isinstance(message, AIMessage):
            # Ignore AI messages that are only making tool calls
            if getattr(message, "tool_calls", None):
                continue

            content = message.content

            if isinstance(content, str):
                draft = content.strip()
            elif isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif isinstance(block, str):
                        text_parts.append(block)
                draft = "\n".join(text_parts).strip()
            else:
                draft = str(content).strip()

            if draft:
                safe_print(f"\n[Draft ready - Attempt {attempt}]\n{'-' * 55}\n{draft}\n{'-' * 55}")
                return {
                    "draft": draft,
                    "attempt": attempt
                }

    safe_print("No draft found.")
    return {
        "draft": "",
        "attempt": attempt
    }


def human_review_node(state: State) -> dict:
    """Pauses the graph and waits for the human to approve or give feedback."""
    attempt = state.get("attempt", 1)
    safe_print(f"\n[Reached human review - Attempt {attempt}]")

    human_response = interrupt({
        "draft": state["draft"],
        "attempt": attempt,
        "instruction": "Type 'approved' to accept, or type your feedback to request a rewrite."
    })

    response = str(human_response).strip()

    if response.lower() in ["approved", "approve", "yes", "ok", "good"]:
        return {
            "is_approved": True,
            "review_feedback": "Approved by human."
        }
    else:
        return {
            "is_approved": False,
            "review_feedback": response
        }


# Router functions
def should_use_tool(state: State):
    """Determines whether the writer made a tool call or generated a draft."""
    last_message = state['messages'][-1]
    if getattr(last_message, 'tool_calls', None):
        safe_print("[Router]: Writer requested Tavily Search tool call.")
        return "tools"
    return "extract_draft"


def should_stop_looping(state: State):
    if state['is_approved']:
        safe_print("\n[Post approved by human. Ending workflow.]")
        return END
    if state['attempt'] >= 3:
        safe_print("\n[Reached max 3 attempts. Ending with last draft.]")
        return END 
    safe_print(f"\n[Rejected. Looping back to writer for attempt {state['attempt'] + 1}...]")
    return "writer"


# build the graph 
graph = StateGraph(State)

graph.add_node("writer", writer_node)
graph.add_node("tools", tool_node)
graph.add_node("extract_draft", extract_draft_node)
graph.add_node("human_review", human_review_node)

# START -> writer
graph.add_edge(START, "writer")

# Writer decides whether to use Tavily tool or extract draft
graph.add_conditional_edges(
    "writer",
    should_use_tool,
    {
        "tools": "tools",
        "extract_draft": "extract_draft"
    }
)

# Tool result goes BACK to writer
graph.add_edge("tools", "writer")

# Extract draft goes to human review
graph.add_edge("extract_draft", "human_review")

# Human review decision loops back to writer or END
graph.add_conditional_edges(
    "human_review",
    should_stop_looping,
    {
        "writer": "writer",
        END: END,
    },
)

checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    safe_print("=" * 55)
    safe_print("Welcome to the LinkedIn Post Generator (HITL Edition)")
    safe_print("=" * 55)
    safe_print("\nThis tool will draft a LinkedIn post for you, show it to")
    safe_print("YOU for review, and rewrite based on your feedback.")
    safe_print("=" * 55)

    if topic := input("\nWhat topic do you want a LinkedIn post about?\n> ").strip():
        safe_print("\nStarting generation...\n")
        config = {"configurable": {"thread_id": "linkedin_session_1"}}

        initial_state = {
            "topic": topic,
            "messages": [],
            "draft": "",
            "review_feedback": "",
            "is_approved": False,
            "attempt": 0,
        }

        result = app.invoke(initial_state, config=config)

        while "__interrupt__" in result:
            interrupt_data = result["__interrupt__"][0].value

            safe_print("\n" + "=" * 55)
            safe_print(f"DRAFT FOR YOUR REVIEW (Attempt {interrupt_data['attempt']})")
            safe_print("=" * 55)
            safe_print(interrupt_data["draft"])
            safe_print("=" * 55)
            safe_print(f"\n{interrupt_data['instruction']}")

            human_input = input("\nYour response: ").strip()

            result = app.invoke(Command(resume=human_input), config=config)

        safe_print("\n" + "=" * 55)
        safe_print("FINAL LINKEDIN POST")
        safe_print("=" * 55)
        safe_print(result["draft"])
        safe_print("=" * 55)
        safe_print(f"Total attempts: {result['attempt']}")
        safe_print(f"Approved by human: {result['is_approved']}")