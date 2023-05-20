from langchain import PromptTemplate

### DOC Sphere PROMPT ###
sys_prompt = """
You are DocQnA bot. User will give you a part of long document as context and a question. 
Rather than making up your own answer, try to find the answer from the context else your response should start with "@error:"
"""
user_prompt = """
Context: {context}
=================
Question: {question}
=================
"""

user_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=user_prompt
)
