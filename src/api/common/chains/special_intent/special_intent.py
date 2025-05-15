from src.api.common.chains.special_intent.intent_processor import SPECIAL_INTENT_MAP


class SpecialIntentProcessor(object):
    def __init__(self, intent_list=None):
        self.special_intent_map = {}
        if isinstance(intent_list, list):
            for intent in intent_list:
                if intent in SPECIAL_INTENT_MAP:
                    module = SPECIAL_INTENT_MAP[intent]()
                    self.special_intent_map[intent] = module
    
    def process(self, prompt_info_dict, **kwargs):
        prompt = prompt_info_dict["prompt_output"]
        intent = prompt_info_dict["intent"]
        if intent in self.special_intent_map:
            return self.special_intent_map[intent].process(prompt, **kwargs)
        else:
            return {
                "skip_llm_call": False,
                "response": "",
                "source_documents": prompt,
                "prompt": []
            }