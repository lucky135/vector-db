from os import getenv
from langchain.schema import Document
import src.api.common.chains.chain_wrapper as chain_wrapper

class TryagainIntent(object):
    def process(self, prompt, **kwargs):
        return {
            "skip_llm_call": False,
            "response": "",
            "source_documents": [],
            "prompt": "please try again"
        }


class DocumentAnalysisIntent(object):
    def process(self, prompt,  **kwargs):
        model_name = getenv("OPENAI_MODEL_NAME")
        prompt_template_key = kwargs.get("prompt_template_key", {})
        language = prompt_template_key.get("language", "english")
        file_name_list = kwargs.get("file_name_list", [])
        vectorstore_wrapper = kwargs.get("vectorstore_wrapper")
        if len(file_name_list) != 1 or vectorstore_wrapper is None:
            print("DocumentAnalysisIntent :: process :: file name or vectorstore is not found")
            return{
                "skip_llm_call": True,
                "response": "As an AI model, I am unable to respond at this time, could you please give more context or select a speific document",
                "source_documents": [],
                "prompt": prompt
            }
        
        chunks, embeddings, metadatas = vectorstore_wrapper.get_texts_from_documents(
            file_name = file_name_list[0]
        )

        if not chunks:
            raise Exception(
                f"[ERROR] - Unable to load text from document {file_name_list[0]}"
            )
        
        # if no embeddings is fetched, generate with embedding model
        if len(embeddings) ==0:
            embeddings = vectorstore_wrapper.embeddings_model.embed_documents(chunks)
        
        global custom_chunks_summary_prompt_template
        global custom_final_summary_prompt_template
        custom_final_summary_prompt_template_str = (
            custom_final_summary_prompt_template.format(
                **{"user_prompt": prompt, "language": language}
            )
        )

        summary = summaries_impl(
            document_list=chunks,
            embeddings=embeddings,
            gpt_model=model_name,
            summary_type="basic",
            language=language,
            chunks_summary_prompt_template=custom_final_summary_prompt_template,
            final_summary_prompt_template=custom_final_summary_prompt_template
        )

        #convert chunks to documents
        source_all_doc = {"page_number": "Page-All", "source": file_name_list[0]}
        source_documents = [Document(page_content="", metadata=source_all_doc)]
        return {
            "skip_llm_call": True,
            "response": summary,
            "source_documents": source_documents,
            "prompt": prompt
        }

class KeywordIntent(object):
    def process(self, prompt, **kwargs):
        file_name_list = kwargs.get("file_name_list", [])
        vectorstore_wrapper = kwargs.get("vectorstore_wrapper")
        if len(file_name_list) != 1 or vectorstore_wrapper is None:
            print("DocumentAnalysisIntent :: process :: file name or vectorstore is not found")
            return{
                "skip_llm_call": True,
                "response": "As an AI model, I am unable to respond at this time, could you please give more context or select a speific document",
                "source_documents": [],
                "prompt": prompt
            }
        
        return {
            "skip_llm_call": False,
            "response": "",
            "source_documents": [],
            "prompt": prompt
        }

SPECIAL_INTENT_MAP = {
    "TryAgainIntent": TryagainIntent,
    "DocumentAnalysisIntent": DocumentAnalysisIntent,
    "KeywordIntent": KeywordIntent
}

        
