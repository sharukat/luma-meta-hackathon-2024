from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.retrievers.multi_query import MultiQueryRetriever
from lib.scraper import Scrape
from lib.text_splitter import SemanticChunker
import torch
import shutil
import os

from flask import Flask, request, jsonify
app = Flask(__name__)


class Chat:
    def __init__(self) -> None:
        self.model_name = "llama3.2:3b"
        self.model = ChatOllama(model = self.model_name)
        self.embedding_function=OllamaEmbeddings(model = self.model_name)
        self.multi_query_llm = ChatOllama(model = "llama3.2:3b")


    def create_db(self, urls: list) -> None:
        if os.path.exists('vectordb'):
            shutil.rmtree('vectordb')
        print("Scrapping..")
        Tool = Scrape()
        docs = Tool.scrape(urls)

        try:
            if docs:
                chunker = SemanticChunker(
                    embeddings=self.embedding_function, 
                    breakpoint_threshold_type="percentile")
                
                chunks = chunker.split_documents(docs)

                vectordb = Chroma.from_documents(
                    documents=chunks,
                    embedding=self.embedding_function,
                    persist_directory='vectordb',
                )
                print("Vector database is created.")
        except Exception as e:
            print(e)
            raise ValueError


    def retriever(self, question: str):
        QUERY_PROMPT = PromptTemplate(
            input_variables=["question"],
            template="""You are an AI language model assistant. Your task is to generate five 
            different versions of the given user question to retrieve relevant documents from a vector 
            database. By generating multiple perspectives on the user question, your goal is to help
            the user overcome some of the limitations of the distance-based similarity search. 
            Provide these alternative questions separated by newlines.
            Original question: {question}""",
        )
        print("Retriving from vector database..")
        vectordb = Chroma(persist_directory='vectordb', 
                      embedding_function=self.embedding_function
                      )

        retriever_from_llm = MultiQueryRetriever.from_llm(
            retriever=vectordb.as_retriever(
                search_type="mmr",
                search_kwargs={'k': 5, 'fetch_k': 20}
            ), 
            llm=self.multi_query_llm,
        )

        docs = retriever_from_llm.invoke(question)
        print("Retrieval completed.")
        return docs


    def generate(self, question: str, urls: list, token: str):
        print(f"Incoming token: {token}")
        torch.cuda.empty_cache()
        context = []
        if token == '0':
            self.create_db(urls)
        else:
            print("Using persisted embeddings.")

        docs = self.retriever(question=question)

        print("Retrieval Successfull")

        for doc in docs:
            context.append(doc.page_content)

        context = "\n\n".join(context)

        prompt = PromptTemplate.from_template(
            """You are an expert on giving information of a website based on the context.

            - Understand the question then let's think step by step.
            - Output a clear and concise response without loosing any relevant information ONLY based on the context.
            - The response will be given to a speech-to-text model to read, therefore maintain the tone.
            `{context}`

            Question:
            `{question}`."""
        )

        chain = prompt | self.model | StrOutputParser()
        response = chain.invoke({"context": context, "question": question})
        return response


@app.route('/generate', methods=['POST'])
def main():
    if request.is_json:
        json_data = request.get_json()
    else:
        json_data = None

    Tool = Chat()
    response = Tool.generate(
        question=json_data['command'],
        urls=json_data['urls'],
        token=json_data['token']
    )
    return jsonify({
        'response': response,
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=50001, debug=True)