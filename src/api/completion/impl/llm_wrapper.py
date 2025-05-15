"""
@author - Krishna Raghav
@copyright - Vector Softwares
"""

from openai import OpenAI
from os import getenv
from src.api.common.logging.Logger import log
from langchain_community.chat_models.openai import ChatOpenAI


def get_openai_api_base(model_name):
    openai_api_key = getenv("OPENAI_API_KEY")
    # if model_name == "gpt-3.5-turbo":
    #     openai_api_key = getenv("OPENAI_API_KEY_GPT_35_TURBO")

    # elif model_name == "gpt-3.5-turbo-16k":
    #     openai_api_key = getenv("OPENAI_API_KEY_GPT_35_TURBO_16K")

    # elif model_name == "gpt-4-turbo":
    #     openai_api_key = getenv("OPENAI_API_KEY_GPT_4_TURBO")

    # elif model_name == "gpt-4-turbo-128k":
    #     openai_api_key = getenv("OPENAI_API_KEY_GPT_4_TURBO_128K")

    # elif model_name == "gpt-4-32k":
    #     openai_api_key = getenv("OPENAI_API_KEY_GPT_4_32K")

    # elif model_name == "gpt-4o":
    #     openai_api_key = getenv("OPENAI_API_KEY_GPT_4O")

    # elif model_name == "gpt-4o-mini":
    #     openai_api_key = getenv("OPENAI_API_KEY_GPT_4O_MINI")

    return openai_api_key


def create_llm(model_name, max_tokens, response_format=None, temperature=0.7, **kwargs):
    """
    Create llm model
    """
    try:
        openai_api_type = getenv("OPENAI_API_TYPE")
        if openai_api_type == "openai":

            llm = ChatOpenAI(
                temperature=temperature,
                max_tokens=max_tokens,
                model=model_name,
                verbose=False,
            )
            return llm
    except ValueError as e:
        print(e.args)
        raise ValueError(f"Invalid model_name: {model_name}")


def create_llm_openai(
    api_key,
    model_name,
    max_token,
    temperature,
    system_message,
    prompt,
    top_p=0.95,
    frequency_penalty=0,
    presence_penalty=0,
    stop=None,
):
    try:
        client = OpenAI(api_key=api_key)
        llm_response = client.chat.completions.create(
            model=model_name,
            max_tokens=max_token,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            stop=stop,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
        )
        llm_response = llm_response.model_dump()
        response = ""
        if llm_response["choices"][0]["message"]["content"] is not None:
            response = llm_response["choices"][0]["message"]["content"]

        log.info("Success generated the response from openai")
        return response
    except ValueError as err:
        log.error(f"Error occurred at llm wrapper :: {err}")
        raise ValueError(f"Invalid model_name: {model_name}")
    except Exception as error:
        log.error(f"Error occurred at llm wrapper :: {error}")
        raise error
