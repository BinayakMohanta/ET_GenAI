from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import operator
from typing import Annotated, TypedDict, List
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import os
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages

# ==========================================
# 1. SETUP API & LLM
# ==========================================
app = FastAPI(title="Healthcare Compliance Agent API")

# Allow web frontends to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to Ollama (support remote Ollama URL via OLLAMA_URL env var)
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY")
)
memory = MemorySaver()

# ==========================================
# 2. LANGGRAPH LOGIC (Your exact code)
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_role: str              
    compliance_audit: List[str] 
    is_compliant: bool          
    last_error: str

def input_guardrail(state: AgentState):
    last_msg = state['messages'][-1].content.lower()
    audit = state.get('compliance_audit', [])
    
    if state.get('user_role') != "Medical_Professional" and any(k in last_msg for k in ["patient", "record", "file", "chart"]):
        audit.append("BLOCK (Access): Non-medical role attempted to access sensitive workflow.")
        return {"is_compliant": False, "compliance_audit": audit, "last_error": "Role-Based Access Denied."}
    
    if any(pii in last_msg for pii in ["ssn", "social security", "dob", "credit card"]):
        audit.append("BLOCK (Privacy): PII detected in user input.")
        return {"is_compliant": False, "compliance_audit": audit, "last_error": "Privacy Violation (PII)."}

    audit.append("PASS (Input): Cleared role and privacy checks.")
    return {"is_compliant": True, "compliance_audit": audit}

def domain_processor(state: AgentState):
    sys_msg = SystemMessage(content=(
        "You are a strictly compliant Healthcare AI. Your job is to provide standard ICD-10 or CPT codes. "
        "RULES: "
        "1. If the user asks for a completely obscure, non-medical, or highly ambiguous condition where you cannot recall the standard code, reply exactly with: 'UNKNOWN_CODE: I require a verified medical registry to confidently answer this.' "
        "2. For standard, well-documented medical conditions, provide the code and you MUST include the word 'Reasoning:' to explain your clinical choice."
    ))
    messages_to_pass = [sys_msg] + state['messages']
    response = llm.invoke(messages_to_pass)
    return {"messages": [response]}

def output_guardrail(state: AgentState):
    last_ai_msg = state['messages'][-1].content
    audit = state['compliance_audit']
    
    if "UNKNOWN_CODE" in last_ai_msg:
        audit.append("BLOCK (Safety Net): Model uncertainty detected. Prevented hallucination.")
        return {"is_compliant": False, "compliance_audit": audit, "last_error": "System Safety: Code could not be verified by LLM memory."}

    if "ICD" not in last_ai_msg.upper() and "CPT" not in last_ai_msg.upper():
        audit.append("BLOCK (Accuracy): Response failed to include standard medical codes.")
        return {"is_compliant": False, "compliance_audit": audit, "last_error": "Accuracy Check Failed: No codes found."}
    
    if "Reasoning:" not in last_ai_msg:
        audit.append("BLOCK (Ethical): AI failed to provide auditable reasoning.")
        return {"is_compliant": False, "compliance_audit": audit, "last_error": "Compliance Failed: Missing audit trail."}
    
    audit.append("PASS (Output): Response verified for accuracy.")
    return {"is_compliant": True, "compliance_audit": audit}

builder = StateGraph(AgentState)
builder.add_node("check_input", input_guardrail)
builder.add_node("process_domain", domain_processor)
builder.add_node("check_output", output_guardrail)

builder.add_edge(START, "check_input")
builder.add_conditional_edges("check_input", lambda s: "process_domain" if s["is_compliant"] else END)
builder.add_edge("process_domain", "check_output")
builder.add_conditional_edges("check_output", lambda s: END)

graph = builder.compile(checkpointer=memory)

# ==========================================
# 3. API ENDPOINT
# ==========================================
class ChatRequest(BaseModel):
    message: str
    role: str
    session_id: str

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        inputs = {
            "messages": [HumanMessage(content=req.message)],
            "user_role": req.role,
            "compliance_audit": [],
            "is_compliant": True,
            "last_error": ""
        }
        
        # Uses session_id so different users don't share memory
        config = {"configurable": {"thread_id": req.session_id}}
        result = graph.invoke(inputs, config=config)
        
        return {
            "is_compliant": result["is_compliant"],
            "response": result["messages"][-1].content if result["is_compliant"] else f"BLOCKED: {result['last_error']}",
            "audit_log": result["compliance_audit"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
