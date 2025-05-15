import tiktoken 

models = {
    "text-embedding-ada-002": {"embedding": 0.0001}
}

def get_num_tokens_from_string(
        text_content: str, model_name="text-embedding-ada-002"
) -> int:
    encoding = tiktoken.encoding_for_model(model_name)
    num_tokens = len(encoding.encode(text_content))
    return num_tokens