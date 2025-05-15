from src.api.common.chains.prompt import prompt_processor_impl
from src.api.common.database.store_handler import store_handler

class PromptProcessor(object):
    def __init__(self, module_list=None, prompt_template=None, persona="", prompt_type=""):
        self.pipeline = []
        if isinstance(module_list, list):
            for module_name in module_list:
                module = getattr(prompt_processor_impl, module_name)()
                self.pipeline.append(module)
        self.prompt_template = prompt_template
        self.persona = persona
        self.prompt_type = prompt_type


    def process(self, prompt:str, **kwargs):
        if not self.pipeline:
            return prompt
        else:
            if self.persona!="" and self.prompt_type!="":
                prompt_details = store_handler.get_all(
                    model_name="Prompt_Library", persona=self.persona, prompt_type=self.prompt_type
                ).first()

                if prompt_details:
                    prompt = prompt_details.prompt_text + prompt
                
            # print(f"==============================================")
            # print(f"PromptProcessor :: process() :: {prompt}")
            # print(f"==============================================")
            
            prompt_info = {
                "prompt_input": prompt,
                "prompt_output": prompt,
                "intent": "",
                "prompt_template": "",
            }

            # proces the prompt with each module in the pipeline
            kwargs["prompt_template"] = self.prompt_template
            for module in self.pipeline:
                prompt_info = module.process(prompt_info, **kwargs)
            return prompt_info