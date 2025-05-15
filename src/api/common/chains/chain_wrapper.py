from src.api.common.chains.prompt.prompt_processor import PromptProcessor
from src.api.common.chains.retrieval_chunks.chunks_processor import ChunksProcessor
from src.api.common.chains.special_intent.special_intent import SpecialIntentProcessor
from src.api.common.chains.chain_template import chain_template
from src.api.common.chains import chain_impl

class ChainWrapper(object):
    def __init__(self, chain_type="exact_answer", persona="", prompt_type="", **kwargs):
        print(f"chain_type :: {chain_type}")
        chain_info = chain_template.get(chain_type)
        if chain_info is None:
            raise Exception(f"No chain type: {chain_type}")
        
        prompt_processor = PromptProcessor(
            module_list=chain_info["prompt"],
            prompt_template=chain_info.get("prompt_template"),
            persona=persona,
            prompt_type=prompt_type
        )

        chunks_processor = ChunksProcessor(
            module_list=chain_info.get("retrieval_chunks")
        )

        special_intent_processor = SpecialIntentProcessor(
            intent_list=chain_info["special_intent"]
        )

        processor_dict = {
            "prompt_processor": prompt_processor,
            "chunks_processor": chunks_processor,
            "special_intent_processor": special_intent_processor
        }

        # create onject from the class defined in the chain_template.py
        chain_class_name = chain_info["chain"]['class']
        print(f"chain_class_name :: {chain_class_name}")
        self.chain = getattr(chain_impl, chain_class_name)(chain_info, processor_dict)
        print(f"chain :: {self.chain}")

    def run(self, llm, prompt, chat_history, **kwargs):
        return self.chain.run(llm, prompt, chat_history, **kwargs)