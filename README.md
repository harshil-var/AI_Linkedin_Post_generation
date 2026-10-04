# 🤖 AI LinkedIn Post Generator

An **Agentic AI LinkedIn Post Generator** built with **LangGraph** that can research a topic, generate a LinkedIn post, review it, and iteratively improve it.

## 🚀 Features

* ✍️ AI-generated LinkedIn posts
* 🔎 Tavily web search for current information
* 🔄 Iterative writing and AI review loop
* 🤖 LLM-based content reviewer
* 👤 Human-in-the-loop review workflow
* 🧠 Conditional routing with LangGraph
* 🔧 Tool calling and agent orchestration
* ⏱️ Maximum retry/attempt control

## 🏗️ Workflow

```text
User Topic
    ↓
Writer Agent
    ↓
Tool Required?
 ┌──┴──┐
Yes    No
 ↓      ↓
Tavily  Draft
 ↓      ↓
Writer  ↓
   └──→ Reviewer
          ↓
      Approved?
       /     \
     Yes      No
      ↓        ↓
     END     Writer
```

The user can also choose between **AI Review** and **Human Review**.

## 🛠️ Tech Stack

* Python
* LangGraph
* LangChain
* Gemini
* Groq
* Tavily Search
* TypedDict
* Human-in-the-Loop

## 🧠 Key LangGraph Concepts

* State management
* Conditional edges
* Tool calling
* Agent loops
* Iterative workflows
* Human-in-the-loop
* Checkpoint-based execution

## ⚠️ Problems I Faced

### 1. Draft was empty

The reviewer was receiving an empty draft.

**Cause:** Incorrect graph flow after the tool call.

**Fix:** Changed:

```text
Tools → Reviewer
```

to:

```text
Tools → Writer → Draft → Reviewer
```

### 2. Gemini returned content as a list

`message.content.strip()` caused an error because Gemini could return structured content blocks.

**Fix:** Added handling for both string and list-based content.

### 3. Gemini API quota exceeded

The Gemini free-tier request limit was reached during repeated writer/tool/review cycles.

**Fix:** Added attempt limits and tested with alternative models/providers.

### 4. Attempt count was incorrect

Tool calls were being counted as new writing attempts.

**Fix:** Separated **tool iterations** from **review/revision attempts**.

### 5. Understanding tool calling

Initially, it was unclear who decides whether Tavily is required.

The final workflow is:

```text
Gemini decides → Tool requested
LangGraph routes → Tavily
Tavily returns → Gemini
Gemini writes → Final Draft
```

## 🎯 Goal

This project demonstrates how **LLMs, tools, conditional routing, automated evaluation, iterative refinement, and human feedback** can be combined to build practical Agentic AI workflows.
