from abc import abstractmethod
import copy
from concurrent.futures import ThreadPoolExecutor

from langchain.chains.llm import LLMChain
from langchain.chains.question_answering import load_qa_chain
from langchain.memory import ConversationBufferWindowMemory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.chains.conversational_retrieval.prompts import CONDENSE_QUESTION_PROMPT
from langchain.chains.constitutional_ai.base import ConstitutionalChain
from langchain_community.callbacks.manager import get_openai_callback

from src.api.common.logging.Logger import log 

NO_ANSWER_STR = "As an AI Language Model, I could not find the response to your question. Please provide me the related context so I can provide more appropriate response"

class BaseChain(object):
    """
    There are 2 ways to make your own chain:
    1. extends some chain in langchain such as COnverstaionalRetrievalChain and use it in the process method.
    2. Put all the details you need into the method process
    """

    def __init__(self, chain_info, process_dict):
        self.prompt_processor = process_dict["prompt_processor"]
        #self.history_processor = process_dict["history_processor"]
        self.special_intent_processor = process_dict["special_intent_processor"]
        self.chunks_processor = process_dict["chunks_processor"]
        self.llmchain = None

    @abstractmethod
    def _create_llmchain(self, llm, **kwargs):
        pass

    @abstractmethod
    def _call_llmchain(self, chat_history_str, docs, prompt_output):
        pass

    def run(self, llm, prompt, chat_history, **kwargs):
        self.verbose = kwargs.get("verbose", False)

        prompt_info_dict = self.prompt_processor.process(prompt, **kwargs)

        print(f"==============================================")
        print(f"Chain_impl :: prompt_info_dict :: {prompt_info_dict}")
        print(f"==============================================")

        processed_prompt = prompt_info_dict["prompt_input"]
        
        kwargs["llm"] = llm

        intent_process_ret = self.special_intent_processor.process(prompt_info_dict, **kwargs)

        if intent_process_ret["skip_llm_call"]:
            return{
                "answer": intent_process_ret["response"],
                "source_documents": intent_process_ret["source_documents"]
            }
        
        #chat_history_str = self.history_processor.process(prompt_info_dict, **kwargs)
        chat_history_str = ""

        chunk_prompt_info_dict = copy.deepcopy(prompt_info_dict)
        chunk_prompt_info_dict['prompt_input'] = prompt
        chunk_prompt_info_dict['prompt_output'] = prompt

        docs = self.chunks_processor.process(chunk_prompt_info_dict, **kwargs)

        print(f"==============================================")
        print(f"Chain_impl :: Filtered Docs :: {docs}")
        print(f"==============================================")

        #create llmchain
        kwargs["chat_history_list"] = chat_history
        kwargs["prompt_info"] = prompt_info_dict
        self._create_llmchain(**kwargs)

        return self._call_llmchain(chat_history_str, docs, processed_prompt)
    

class CombinedDocumentConversationChain(BaseChain):
    def __init__(self, chain_info, processor_dict):
        super().__init__(chain_info, processor_dict)
        self.qa_chain_type = chain_info["chain"].get("qa_chain_type", "stuff")
    
    def _create_llmchain(self, **kwargs):
        llm = kwargs.get("llm")

        # Create llm chain for question generation 
        self.condense_question_chain = LLMChain(
            llm=llm, prompt=CONDENSE_QUESTION_PROMPT, verbose = self.verbose
        )

        # create llm chain for question answering
        self.llmchain = load_qa_chain(
            llm, chain_type=self.qa_chain_type, verbose = self.verbose
        )

    def _call_llmchain(self, chat_history_str, docs, prompt_output):
        # check chat history and retrieval chunks
        if len(chat_history_str) == 0 and len(docs) ==0:
            return {"answer": NO_ANSWER_STR, "source_documents": []}
        
        # generate new question with original question and chat history
        if chat_history_str:
            new_question = self.condense_question_chain.run(
                question=prompt_output, chat_history=chat_history_str
            )
        else:
            new_question = prompt_output

        # run with llm chain: the prompt template should contains 2keys ['question', 'chat_history']
        new_inputs = {"question": new_question, "chat_history": chat_history_str}
        answer = self.llmchain.run(input_documents=docs, **new_inputs)

        output = {"answer": answer, "source_documents": docs}

        return output


class BaseConversationChain(BaseChain):
    def _create_llmchain(self, **kwargs):
        prompt_info = kwargs.get("prompt_info", {})
        prompt_template = prompt_info.get("prompt_template", "")
        # print(f"==============================================")
        # print(f"prompt_template :: {prompt_template}")
        # print(f"==============================================")

        # build conversational memory for llm
        messages = kwargs.get("chat_history_list", [])
        memory = ConversationBufferWindowMemory(
            k=5,
            input_key="chat_history",
            chat_memory=ChatMessageHistory(messages=messages)
        )

        #build llm
        llm = kwargs.get("llm")

        print(f"llm :: {llm}")
        print(f"memory :: {memory}")

        self.llmchain = LLMChain(
            llm=llm, memory=memory, prompt=prompt_template, verbose=self.verbose
        )

        print(f"llmchain :: {self.llmchain}")
        
        
        # build constitutional chain for the custom principles if needed
        constitutional_ai_princinple = kwargs.get("constitutional_ai_princinple")
        if(constitutional_ai_princinple is not None):
            self.llmchain = ConstitutionalChain.from_llm(
                chain=self.llmchain,
                constitutional_principles=constitutional_ai_princinple,
                llm=llm,
                verbose=self.verbose
            )


    def _call_llmchain(self, chat_history_str, docs, prompt_output):
        answer = self.llmchain.run(input=prompt_output, chat_history=chat_history_str)
        print(f"answer :: {answer} ")
        output = {"answer": answer, "source_documents": docs}
        return output


class RetrievalConversationChain(BaseConversationChain):
    def _call_llmchain(self, chat_history_str, docs, prompt_output):
        context_str = "\n\n".join(doc.page_content for doc in docs)

        # print(f"==============================================")
        # print(f"RetrievalConversationChain :: context_str :: {context_str}")
        # print(f"==============================================")
      
        answer = self.llmchain.run(
            input=prompt_output, chat_history=chat_history_str, context=context_str
        )
        output = {"answer": answer, "source_documents": docs}
        return output
