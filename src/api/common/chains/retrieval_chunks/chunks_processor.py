from os import getenv
from langchain.docstore.document import Document

from src.api.common.chains.retrieval_chunks import chunks_processor_impl
from src.api.completion.impl.llm_wrapper import create_llm

class ChunksProcessor(object):
    def __init__(self, module_list=None):
        print(f"Initializing the chunk processor...")
        self.pipeline = []
        if isinstance(module_list, list):
            for module_name in module_list:
                module = getattr(chunks_processor_impl, module_name)()
                self.pipeline.append(module)
    
    def process(self, prompt_info, **kwargs):

        vectorstore_wrapper = kwargs.get("vectorstore_wrapper")
        file_name_list = kwargs.get("file_name_list", [])

        print(f"==============================================")
        print(f"Executing ChunksProcessor :: process() :: prompt_info :: {prompt_info}")
        print(f"==============================================")

        if vectorstore_wrapper is None:
            return []
        
        prompt = prompt_info["prompt_input"]
        # If the intent of prompt belongs to document related intents ['KeywordIntent']
        # then we will retrieve all the chunks from the document else we will return
        # only the relevant chunks
        if (
            prompt_info["intent"] in ["KeywordIntent", "TranslateIntent"]
            and len(file_name_list) == 1
        ):
            file_name = file_name_list[0]
            chunks, _, metadatas = vectorstore_wrapper.get_texts_from_documents(
                file_name=file_name
            )

            # print(f"==============================================")
            # print(f"Executing ChunksProcessor :: process() :: chunks 1 :: {chunks}")
            # print(f"==============================================")


            # convert chunks to documents
            chunks = [
                Document(page_content=chunk, metadata=metadata)
                for chunk, metadata in zip(chunks, metadatas)
            ]
        else:
            llm = create_llm(
                model_name=getenv("OPENAI_MODEL_NAME"),
                max_tokens=4000,
                temperature=0.7
            )
            retriever_threshold = kwargs.get("retriever_threshold", 0.7)
            retriever = vectorstore_wrapper.get_retrieve(
                file_name_list = file_name_list,
                retriever_threshold = retriever_threshold,
                llm=llm
            )
            if retriever is None:
                chunks = []
            else:
                chunks = retriever.get_relevant_documents(prompt)
            
            # print(f"==============================================")
            # print(f"Executing ChunksProcessor :: process() :: chunks 2:: {chunks}")
            # print(f"==============================================")

        if not self.pipeline:
            return chunks
        else:
            for module in self.pipeline:
                chunks = module.process(chunks, prompt, **kwargs)
            return chunks