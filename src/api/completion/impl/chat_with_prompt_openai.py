"""
@author - Krishna Raghav
@copyright - Vector Softwares
"""

import json
import uuid
from src.api.common.logging.Logger import log
from src.api.completion.impl.llm_wrapper import get_openai_api_base
from src.api.completion.impl.llm_wrapper import create_llm_openai, create_llm
from src.api.common.constitutional_principle.ai_constitutional_principle import (
    is_safe_response,
    check_fairness,
)
from src.api.common.database.store_handler import store_handler
from src.api.common.chains.chain_wrapper import ChainWrapper
from langchain_community.callbacks.manager import get_openai_callback


def chat_with_prompt_openai(
    response_format: str,
    prompt: str,
    chat_type: str,
    user_details: any,
    chat_id: str,
    persona: str,
    prompt_type: str,
    gpt_model: str,
    temperature: float,
    max_token: int,
    opt_out: bool = False,
    summary_required: str = "yes",
    lanaguage: str = "english",
    constitutional_ai_princinple: list = None,
    system_message: str = "",
    openai_api_base="",
    openai_api_key="",
    openai_api_version="",
) -> str:
    """
    Return chat prompt answer using Chatgpt API

    :param str prompt: prompt
    :param str chat_id: unique identifier for a chat, this would map to multiple conversations with the bot
    :param str persona: persona
    :param str gpt_model: gpt_model
    :param float temperature: temperature between 0.0 and 1.0
    :param int max_token: max_token
    :param str opt_out: opt_out
    :param str summary_required: summary_required
    :param str lanaguage: lanaguage
    :param str constitutional_ai_princinple: constitutional_ai_princinple
    :param str system_message: system_message

    :return str response: prompt answer
    :rtype str

    """

    # We will use user_detail in future to manage multiple chats for a user in one session

    response = {}
    model_name = gpt_model
    lanaguage = lanaguage.lower()

    log.info(f"[INFO]: Using model: {model_name} and persona {persona}")
    log.info(
        f"[INFO]: Initializing Chat model with temperature = {temperature} and max_token: {max_token}"
    )

    try:
        prompt_details = store_handler.get_all(
            model_name="Prompt_Library", persona=persona, prompt_type=prompt_type
        ).first()

        if system_message == "" and prompt_details:
            system_message = prompt_details.persona_base_prompt

        # add prefix conceptual prompt to data
        if prompt_details:
            prompt_context = prompt_details.prompt_text
            prompt = prompt_context.replace("[USER_INPUT]", prompt)
            prompt = prompt + "\n\n" + prompt_details.output_format_prompt

        top_p: float = 0.95
        presence_penalty: float = 0
        frequency_penalty: float = 0
        stop: str = None

        # TODO: Load chathistory from database

        llm = create_llm(
            model_name=model_name,
            max_tokens=max_token,
            temperature=temperature,
            response_format=response_format,
            openai_api_key=openai_api_key,
            openai_api_base=openai_api_base,
            openai_api_version=openai_api_version,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
        )

        print(f"Initialized the llm : {llm}")

        chain_type = "prompt_conversation_chain"
        llmchain = ChainWrapper(chain_type=chain_type)
        print(f"Initialized the llmchain : {llmchain}")
        try:
            with get_openai_callback() as cb:
                log.info(f"Calling LLM for prediction...")
                kwargs = {
                    "prompt_template_key": {"language": lanaguage, "persona": persona},
                    "user_prompt_template": {"system": system_message},
                    "constitutional_ai_principle": constitutional_ai_princinple,
                }
                result = llmchain.run(llm=llm, prompt=prompt, chat_history=[], **kwargs)
            output = result["answer"]
        except Exception as e:
            log.error(
                f"Error occured at chat_with_prompt_openai :: {e} - [ERROR CODE] - 'ER-PRSMCP-019",
                exc_traceback=e.__traceback__,
            )
            raise e

        # apply constitutional principles
        if not is_safe_response(output):
            raise ValueError("Unsafe response detected.")

        if not check_fairness(output):
            raise ValueError("Unfair or biased response detected.")

    except Exception as err:
        log.error(
            f"Error occured at chat_with_prompt_openai :: {err} - [ERROR CODE] - 'ER-PRSMCP-020",
            exc_traceback=err.__traceback__,
        )
        raise err

    # TODO: add chat history in database and generate the chat_id

    chat_id = uuid.uuid4()

    return output, chat_id


def chat_with_prompt_openai_prev(
    response_format: str,
    prompt: str,
    chat_type: str,
    user_details: any,
    chat_id: str,
    persona: str,
    gpt_model: str,
    temperature: float,
    max_token: int,
    opt_out: bool = False,
    summary_required: str = "yes",
    lanaguage: str = "english",
    constitutional_ai_princinple: list = None,
    system_message: str = "",
) -> str:
    """
    Return chat prompt answer using Chatgpt API

    :param str prompt: prompt
    :param str chat_id: unique identifier for a chat, this would map to multiple conversations with the bot
    :param str persona: persona
    :param str gpt_model: gpt_model
    :param float temperature: temperature between 0.0 and 1.0
    :param int max_token: max_token
    :param str opt_out: opt_out
    :param str summary_required: summary_required
    :param str lanaguage: lanaguage
    :param str constitutional_ai_princinple: constitutional_ai_princinple
    :param str system_message: system_message

    :return str response: prompt answer
    :rtype str

    """

    # We will use user_detail in future to manage multiple chats for a user in one session

    response = {}
    model_name = gpt_model
    lanaguage = lanaguage.lower()

    log.info(f"[INFO]: Using model: {model_name}")
    log.info(
        f"[INFO]: Initializing Chat model with temperature = {temperature} and max_token: {max_token}"
    )

    try:
        prompt_details = store_handler.get_all(
            model_name="Prompt_Library", persona=persona
        ).first()

        if system_message == "" and prompt_details:
            system_message = prompt_details.get("persona_base_prompt", "")

        # add prefix conceptual prompt to data
        if prompt_details:
            prompt = prompt_details.get("prompt_text", "") + prompt

        top_p: float = 0.95
        presence_penalty: float = 0
        frequency_penalty: float = 0
        stop: str = None

        # TODO: Load chathistory from database

        openai_api_key = get_openai_api_base(gpt_model)

        response = create_llm_openai(
            openai_api_key,
            model_name=model_name,
            max_token=max_token,
            temperature=temperature,
            system_message=system_message,
            prompt=prompt,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            stop=stop,
        )

        output = response

        # apply constitutional principles
        if not is_safe_response(output):
            raise ValueError("Unsafe response detected.")

        if not check_fairness(output):
            raise ValueError("Unfair or biased response detected.")

    except Exception as err:
        log.error(
            f"Error occured at chat_with_prompt_openai :: {err} - [ERROR CODE] - 'ER-PRSMCP-018",
            exc_traceback=err.__traceback__,
        )
        raise err

    # TODO: add chat history in database and generate the chat_id

    chat_id = uuid.uuid4()

    return output, chat_id
