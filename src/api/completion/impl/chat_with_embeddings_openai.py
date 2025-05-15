import json
import os
import uuid
from collections import defaultdict

from langchain_community.callbacks.manager import get_openai_callback

from src.api.common.logging.Logger import log 
from src.api.common.database.store_handler import store_handler
from src.api.common.vectorstore.vectorstore import VectorStoreWrapper
from src.api.completion.impl.llm_wrapper import create_llm
from src.api.common.chains.chain_wrapper import ChainWrapper

def chat_with_embedding_openai(
        prompt: str,
        chat_id: str,
        index_search: str,
        gpt_model: str,
        temperature: float,
        max_tokens: int,
        retriever_threshold_type: str,
        retriever_type: str,
        file_name_list: list,
        collection_name: str,
        persona: str,
        prompt_type: str,
        chat_type: str = "document_chat",
        chain_type: str = "",
        opt_out: bool = False,
        format_styling_flag="MARKUP",
        language: str = "english",
        system_message: str = "",
        response_format=None,
        openai_api_base="",
        openai_api_key="",
        openai_api_version="",
        frequency_penalty: int = 0,
        presence_penalty: int = 0
):
    """
    Return chat prompt answer from ChatOpenAI LLM ans sourdces from vectorstore.

    Parameters:
    - prompt : prompt
    - chat_id: unique id of the chat
    - gpt_model: gpt model,
    - chat_type: chat type,
    - temperature: temperature between 0.0 and 1.0
    - mas_tokens: max output tokens of gpt model
    - langauge: output language

    Return: prompt answer, verified sources, conversation id
    """

    model_name = gpt_model
    language = language.lower()

    prompt_details = store_handler.get_all(
        model_name="Prompt_Library", persona=persona, prompt_type=prompt_type
    ).first()
        
    if system_message == "" and prompt_details:
        system_message = prompt_details.persona_base_prompt
        
    # add prefix conceptual prompt to data
    # Commenting it as it creates problem with document retreival
    # if prompt_details:
    #     prompt = prompt_details.prompt_text + prompt

    log.info(f"Using model : {model_name}")

    llm = create_llm(
        model_name=model_name,
        max_tokens=max_tokens,
        temperature=temperature,
        response_format=response_format,
        openai_api_base=openai_api_base,
        openai_api_key=openai_api_key,
        openai_api_version=openai_api_version,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty
    )

    vectorstore_wrapper = VectorStoreWrapper(
        collection_name=collection_name,
        retriever_type=retriever_type,
        openai_api_base=openai_api_base,
        openai_api_key=openai_api_key,
        openai_api_version=openai_api_version,
    )

    # build retrieval conversation chain
    chain_type, retrieval_threshold = get_chain_type_retriever_threshold(
        chain_type, retriever_threshold_type, gpt_model
    )

    log.info(f"chain_type = {chain_type}, retriever_threshold = {retrieval_threshold}")
    llmchain = ChainWrapper(chain_type=chain_type, persona=persona, prompt_type=prompt_type)

    try:
        with get_openai_callback() as cb:
            log.info("Calling LLM for prediction..")
            kwargs = {
                "vectorstore_wrapper": vectorstore_wrapper,
                "prompt_template_key": {"language": language},
                "file_name_list": file_name_list,
                "retriever_threshold": retrieval_threshold,
                "user_prompt_template": {"system": system_message}
            }

            result = llmchain.run(
                llm=llm, prompt=prompt, chat_history=[], **kwargs
            )

            if "openai_callback" in result:
                total_token = result["openai_callback"]["total_token"]
            else:
                total_token = cb.total_tokens
            
            answer = result["answer"]
    except Exception as e:
        log.error(
            message=f"{e}", exc_traceback=e.__traceback__
        )

        if "This model's maximum context length is" in e.args[0]:
            raise Exception(e.args[0])
        else:
            raise
        result = {"source_documents": []}
        total_token = cb.total_token
    
    verified_sources, source_data = get_docs_source(
        docs=result["source_documents"]
    )

    # Not saving the convesation in database as of now so generating a random conversation id
    conversation_id = uuid.uuid4()
    # if not opt_out:
    #     conversation_id = save_chat_to_db(
    #         chat_id=chat_id,
    #         chat_type=chat_type,
    #         prompt=prompt,
    #         response=answer,
    #         model_user=model_name,
    #         sources=verified_sources
    #     )

    answer = answer.replace("\n\n", "\n")

    return answer, verified_sources, conversation_id, source_data



def get_chain_type_retriever_threshold(
        chain_type: str, retriever_threshold_type: str, gpt_model: str
):
    retriever_threshold_info = {
        "Low": 0.6,
        "Medium": 0.7,
        "High": 0.8
    }

    chain_mapping_info = {
        "exact_answer_map_reduce_special_intention": "non_exact_answer_special_intention",
        "exact_answer_stuff_special_intention": "non_exact_answer_special_intention",
        "exact_answer_map_reduce": "non_exact_answer"
    }

    if gpt_model == "gpt-4" and retriever_threshold_type == "High":
        retriever_threshold_type = "Medium"
    
    retriever_threshold = retriever_threshold_info.get(retriever_threshold_type, 0.7)

    if chain_type == "":
        if retriever_threshold_type in ["Low", "Medium"]:
            chain_type = "non_exact_answer_special_intention"
        else:
            chain_type = "exact_answer_map_reduce_special_intention"
    else:
        if gpt_model == "gpt-4" and chain_type in chain_mapping_info:
            chain_type = chain_mapping_info[chain_type]
    return chain_type, retriever_threshold


def get_docs_source(docs):
    """
    Get relevant documents from response
    """
    source_page_dict = defaultdict(dict)
    for idx, doc in enumerate(docs):
        source = doc.metadata["source"]
        page_content = doc.page_content

        _, file_extension = os.path.splitext(source)
        if file_extension not in [".docx", ".doc", ".txt"]:
            page = doc.metadata["page_number"]
        else:
            page = f"Page-{idx+1}"
        
        page_data_dict = source_page_dict[source]
        if page in page_data_dict:
            page_data_dict[page].append(page_content)
        else:
            page_data_dict[page] = [page_content]
        

    source_page_list = [
        f'{key}: {", ".join(page_data_dict.keys())}'
        for key, page_data_dict in source_page_dict.items()
    ]

    verified_sources = source_page_list

    source_data = [
        {
            "file_name": "Your previous chats and model's intelligence",
            "data": [{"page_number": "", "data": ""}]
        }
    ]

    if source_page_dict:
        source_data = []
        for file_name, page_data_dict in source_page_dict.items():
            data = []
            for page_number, page_data in page_data_dict.items():
                data.append({"page_number": page_number, "data": " ".join(page_data)})
            source_data.append({"file_name": file_name, "data": data})
    
    return verified_sources, source_data