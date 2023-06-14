import asyncio

from VectorStore import VectorStore
from config import OPENAI_API_KEY
from prompt import sys_prompt, user_prompt
from openAiApi import OpenAIAPI


class Bot:
    def __init__(self, openai_api, vectorStore):
        self.openai_api = openai_api
        self.vectorStore = vectorStore

    def digestDoc(self, userId, doc, docId):
        self.vectorStore.store(userId, doc, docId)

    async def getAnswer(self, userId, ques, k=2):
        # Step 1: Get the context from the vector store
        # context = self.vectorStore.cosine_similarity_search(userId, ques, k)
        context = self.vectorStore.hybrid_similarity_search(userId, ques, k)

        print(context)

        # Create an empty reference list
        reference_list = []

        # Iterate over the documents list
        for document in context:
            # Add the document's UUID and page number to the reference list
            # Convert the UUID object to a string using str()
            reference_list.append({'link': str(document['url']), 'pageNo': document['pageNo']})

        # Step 2: Get the answer using OpenAI
        messages = [
            {
                "role": "system",
                "content": sys_prompt,
            },
            {
                "role": "user",
                "content": user_prompt.format(context=context, question=ques)
            }
        ]
        # print(messages)
        completion = await self.openai_api.chat_completion(
            model="gpt-4",
            messages=messages,
            temperature=0.0,
            max_tokens=512,
        )
        ans = completion.choices[0].message["content"]

        # Step 3: Return ant answer with reference
        return {"answer": ans, "reference": reference_list}


#
# usage
# import asyncio
#
# vectorStore = VectorStore('Persistence/vector_store.pkl')
# userId = 'user1'
# openai_api = OpenAIAPI(OPENAI_API_KEY)
# bot = Bot(openai_api, vectorStore)
# bot.digestDoc(userId, "./Docs/TestDoc.pdf")
#
# async def main():
#     print("Please enter your query")
#     query = input()
#     print("Please enter the number of results you want")
#     k = int(input())
#     result = await bot.getAnswer(userId, query, k)
#
#     print(result)
#
#
# asyncio.run(main())
#
#
# import gradio as gr
# import asyncio
#
# # Assume bot is an instance of the Bot class defined in the code
# # Assume userId is a global variable that identifies the user
#
# # Define a function that takes a document as input and calls the digestDoc method of the bot
# def digest_doc(doc):
#   # Assume doc is a file object that can be read by some library
#   bot.digestDoc(userId, doc)
#   return "Document digested successfully"
#
# # Define a function that takes a question and a number of results as inputs and calls the getAnswer method of the bot
# def get_answer(question, k):
#   # Use asyncio to run the async getAnswer method
#   result = asyncio.run(bot.getAnswer(userId, question, k))
#   return result
#
# # Define some custom CSS for the interface
# css = """
# #col-container {max-width: 700px; margin-left: auto; margin-right: auto;}
# """
#
# # Define some HTML for the title of the interface
# title = """
# <div style="text-align: center;max-width: 700px;">
#  <h1>Chat with PDF • Bot</h1>
#  <p style="text-align: center;">Upload a .PDF from your computer, click the "Load PDF to Bot" button, <br />
#  when everything is ready, you can start asking questions about the pdf ;) <br />
#  This version is set to store chat history, and uses your bot as LLM</p>
# </div>
# """
#
# # Create a gradio interface with one input and one output for the document digestion
# digest_iface = gr.Interface(
#   fn = digest_doc, # The function to call
#   inputs = gr.inputs.File(label="Load a document", type=".pdf,.docx,.png,.jpg"), # A file input for the document that accepts pdf, docx, png and jpg files
#   outputs = gr.outputs.Textbox(label="Digestion status") # A textbox for the output
# )
#
#
# # Create a gradio interface with two inputs and one output for the question answering
# answer_iface = gr.Interface(
#   fn = get_answer, # The function to call
#   inputs = [gr.inputs.Textbox(label="Please enter your question"), # A textbox for the question
#             gr.inputs.Slider(minimum=1, maximum=10, default=5, label="Please enter the number of results you want")], # A slider for the number of results
#   outputs = gr.outputs.Textbox(label="Bot answer") # A textbox for the output
# )
#
# # Create a container to hold both interfaces
# container = gr.Container(
#   [digest_iface, answer_iface], # The list of interfaces to display
#   title = title, # The title of the container
#   layout = "horizontal", # Use a horizontal layout for the container
#   css=css # Use the custom CSS for the container
# )
#
# # Launch the container
# container.launch()
