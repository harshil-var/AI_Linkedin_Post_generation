import os 
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from dotenv import load_dotenv


load_dotenv()

#tools 

search_tool = TavilySearch(max_results = 3)


tools = [search_tool]

#llms 

#writer
writer_llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

writer_llm_with_tools = writer_llm.bind_tools(tools)

#reviewer

reviewer_llm = ChatGroq(model="openai/gpt-oss-20b")

#state building 

class State(TypedDict):
    topic : str 
    messages : Annotated[list,add_messages]
    draft : str 
    review_feedback : str
    is_approved : bool 
    attempt : int


#nodes 

WRITER_SYSTEM_PROMPT = (
    """
    You are an expert LinkedIn content writer.

    Write engaging, professional LinkedIn posts.

    Rules:
    - Strong hook in the first line
    - One clear takeaway
    - Short paragraphs
    - Around 150-200 words
    - End with a question or CTA
    - Professional but human
    - No hashtags
    - Return ONLY the LinkedIn post
    - Never explain your reasoning
    - Never mention the reviewer
    - Never mention prompts
    - Never mention feedback
    - Never add introductory text such as "Here is your post"
    """
)


def writer_node(state: State) -> dict:

    topic = state["topic"]
    feedback = state.get("review_feedback", "")
    messages = state.get("messages", [])

    # If returning from a tool call, pass full conversation history (SystemMessage + messages) to the LLM
    if messages and getattr(messages[-1], "type", None) == "tool":
        prompt_messages = [SystemMessage(content=WRITER_SYSTEM_PROMPT)] + list(messages)
        response = writer_llm_with_tools.invoke(prompt_messages)
        return {
            "messages": [response]
        }

    if feedback:
        user_message_text = f"""
        Rewrite the LinkedIn post about:
        {topic}
        The reviewer gave this feedback:
        {feedback}

        Fix every issue mentioned by the reviewer.

        Return ONLY the new LinkedIn post.
        Do not mention the reviewer.
        Do not mention the previous draft.
        Do not explain your reasoning.
        """
    else:
        user_message_text = f"""
        Write a LinkedIn post about:
        {topic}

        If current information is necessary, use the web search tool.

        Return ONLY the final LinkedIn post.
        Do not explain your reasoning.
        Do not mention reviewer feedback.
        """

    human_msg = HumanMessage(content=user_message_text)
    system_msg = SystemMessage(content=WRITER_SYSTEM_PROMPT)

    response = writer_llm_with_tools.invoke([system_msg, human_msg])

    return {
        "messages": [human_msg, response]
    }

    print("\n========== WRITER RESPONSE ==========")
    print(response)
    print("=====================================\n")

    print("CONTENT:")
    print(response.content)

    print("TOOL CALLS:")
    print(response.tool_calls)

tool_node = ToolNode(tools)

def extract_draft_node(state: State) -> dict:
    """Extract the final text response from the writer."""

    for message in reversed(state["messages"]):

        if isinstance(message, AIMessage):

            # Ignore AI messages that are only making tool calls
            if getattr(message, "tool_calls", None):
                continue

            content = message.content

            # Gemini may return content as a string
            if isinstance(content, str):
                draft = content.strip()

            # Gemini may return content as a list of blocks
            elif isinstance(content, list):

                text_parts = []

                for block in content:

                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            text_parts.append(block.get("text", ""))

                    elif isinstance(block, str):
                        text_parts.append(block)

                draft = "\n".join(text_parts).strip()

            else:
                draft = str(content).strip()

            if draft:
                print("\n" + "=" * 50)
                print("GENERATED LINKEDIN POST")
                print("=" * 50)
                print(draft)
                print("=" * 50)

                return {
                    "draft": draft
                }

    print("No draft found.")

    return {
        "draft": ""
    }
    

REVIEWER_SYSTEM_PROMPT = (
    "You are a strict LinkedIn content reviewer. You judge whether a "
    "post is publish-ready. Evaluate against these criteria:\n"
    "1. Strong hook in the first line\n"
    "2. One clear, valuable takeaway\n"
    "3. Easy to skim — uses short paragraphs\n"
    "4. Roughly 150-200 words\n"
    "5. Ends with an engaging question or CTA\n"
    "6. Professional but human tone (not corporate-robotic)\n"
    "7. No hashtags\n\n"
    "Respond in exactly this format:\n"
    "VERDICT: APPROVED or REJECTED\n"
    "FEEDBACK: <one short paragraph explaining why>\n\n"
    "Be strict but fair. Approve only if the post genuinely meets all "
    "criteria. Reject if even one criterion is clearly missing."
)

def reviewer_node(state: State) -> dict:

    draft = state["draft"]

    prompt = f"""
    Review this LinkedIn post:
    {draft} """

    response = reviewer_llm.invoke([
        ("system", REVIEWER_SYSTEM_PROMPT),
        ("human", prompt)
    ])

    review_text = response.content.strip()

    is_approved = "VERDICT: APPROVED" in review_text.upper()

    if "FEEDBACK:" in review_text:
        feedback = review_text.split("FEEDBACK:", 1)[1].strip()
    else:
        feedback = review_text

    return {
        "review_feedback": feedback,
        "is_approved": is_approved,
        "attempt": state.get("attempt", 0) + 1
    }

#router function 

def should_use_tool(state:State):
    last_message = state['messages'][-1]

    if getattr(last_message,'tool_calls',None):
        return "tools"
    return "extract_draft"

def should_stop_looping(state:State):
    if state['is_approved']:
        print("post haas been approved \n")
        return END
    if state['attempt'] >= 3:
        print("reached max attempts")
        return END 
    return "writer"


#build the graph 
graph = StateGraph(State)

graph.add_node("writer", writer_node)
graph.add_node("tools", tool_node)
graph.add_node("extract_draft", extract_draft_node)
graph.add_node("reviewer", reviewer_node)

# START
graph.add_edge(START, "writer")

# Writer decides whether to use Tavily
graph.add_conditional_edges(
    "writer",
    should_use_tool,
    {
        "tools": "tools",
        "extract_draft": "extract_draft"
    }
)

# IMPORTANT:
# Tool result goes BACK to writer
graph.add_edge("tools", "writer")

# Once final text is available
graph.add_edge("extract_draft", "reviewer")

# Reviewer decides whether to stop or rewrite
graph.add_conditional_edges(
    "reviewer",
    should_stop_looping,
    {
        "writer": "writer",
        END: END
    }
)

app = graph.compile()


if __name__ == "__main__":
    print("=" * 55)
    print("Welcome to the LinkedIn Post Generator")
    print("=" * 55)
    print("\nThis tool will draft a LinkedIn post for you, review it")
    print("itself, and iterate until it's publish-ready.")

    print("=" * 55)

    topic = input("\nWhat topic do you want a LinkedIn post about?\n> ").strip()

    if not topic:
        print("\nNo topic given. Exiting.")
    else:
        print("\nStarting generation...\n")

        initial_state = {
            "topic": topic,
            "messages": [],
            "draft": "",
            "review_feedback": "",
            "is_approved": False,
            "attempt": 0,
        }

        final_state = app.invoke(initial_state)

        print("\n" + "=" * 55)
        print("FINAL LINKEDIN POST")
        print("=" * 55)
        print(final_state["draft"])
        print("=" * 55)
        print(f"Total attempts: {final_state['attempt']}")
        print(f"Approved: {final_state['is_approved']}")