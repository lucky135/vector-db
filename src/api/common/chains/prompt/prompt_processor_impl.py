from os import getenv
from abc import abstractmethod

from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import ChatPromptTemplate

from src.api.completion.impl.llm_wrapper import create_llm
from src.api.completion.impl.prompt_considerations import (
    get_prompt_prefix,
    prompt_prefix_map
)
from src.api.common.chains.prompt.prompt_template import prompt_template_map

class BasePromptProcessor(object):
    model_name = getenv("OPENAI_MODEL_NAME")

    @abstractmethod
    def process(self, prompt: str, **kwargs):
        return prompt

word_limit_intention_prompt_template = """
Here are some examples:

input: Where is China?
please tell whether the input mentions the maximum word limit.
output: no

input: Could you tell me what is in this Document? Please reply with more than 200 words.
please tell whether the input mentions the maximum word limit.
output: no

input: Is there any evident to it? please reply with more than 50 words
please tell whether the input mentions the maximum word limit.
output: no

input: Where is China? Please reply with less than 100 words.
please tell whether the input mentions the maximum word limit.
output: yes

input: {question}
please tell whether the input mentions the maximum word limit.
output:

"""

intent_prompt_template = """
Here are some intentions:
1. document analysis
2. translate
3. try again
4. other

input: Where is China:
please tell me which given intention of the input is
output: other

input: Can you tell what is AWS:
please tell me which given intention of the input is
output: other

input: I want summary of the document:
please tell me which given intention of the input is
output: document analysis

input: Can yo provide the hsn code from the document:
please tell me which given intention of the input is
output: document analysis

input: Can you translate the text into hindi langauge:
please tell me which given intention of the input is
output: translate

input: Could you please try again:
please tell me which given intention of the input is
output: try again

input: Describe the context:
please tell me which given intention of the input is
output: document analysis

input: {question}
please tell me which given intention of the input is
output:


"""

class ExpansionPromptProcessor(BasePromptProcessor):
    def _create_prompt_template(self):
        prompt = PromptTemplate(
            input_variables=["question"], template=word_limit_intention_prompt_template
        )
        return prompt
    
    def process(self, prompt_info: dict, **kwargs):
        llm = create_llm(model_name=self.model_name, max_tokens=3000, temperature=0)
        prompt_template = self._create_prompt_template()

        chain = LLMChain(llm=llm, prompt=prompt_template)
        prompt = prompt_info["prompt_input"]
        intention = chain.run({"question": prompt})
        if intention=="no":
            prompt += "\n Please elaborate."
        prompt_info["prompt_output"] = prompt
        return prompt_info
    
intent_map = {
    "document_analysis": "DocumentAnalysisIntent",
    "translate": "TranslateIntent"
}

class SpecificIntentionPromptProcessor(BasePromptProcessor):
    def _create_prompt_template(self):
        prompt = PromptTemplate(
            input_variables=["question"], template=intent_prompt_template
        )
        return prompt
    
    def process(self, prompt_info: dict, **kwargs):
        llm = create_llm(model_name=self.model_name, max_tokens=4000, temperature=0.7)
        prompt_template = self._create_prompt_template()

        chain = LLMChain(llm=llm, prompt=prompt_template)
        prompt = prompt_info["prompt_output"]
        intention = chain.run({"question": prompt})
        if intention in intent_map:
            prompt_info["intent"] = intent_map[intention]
        
        file_name_list = kwargs.get("file_name_list", [])
        if len(file_name_list) != 1:
            prompt_info["intent"] = ""
        return prompt_info

class PromptTemplateProcessor(BasePromptProcessor):
    def _get_prompt_template_str(
        self,
        user_prompt_template_info,
        prompt_template_info,
        prompt_template_key,
        prompt_type="system"
    ):
        if user_prompt_template_info.get(prompt_type, "") !="":
            prompt_template_str = user_prompt_template_info[prompt_type]
            prompt_template_str = prompt_template_str.replace("{", " [ ")
            prompt_template_str = prompt_template_str.replace("}", " ] ")

            return prompt_template_str
        
        if prompt_template_info[prompt_type] in prompt_template_map:
            template_key = prompt_template_info[prompt_type]
        else:
            template_key = (
                "default_system_prompt_template" if prompt_type == "system" else "default_human_prompt_template"
            )
        
        prompt_template_str = prompt_template_map[template_key].format(**prompt_template_key)

        return prompt_template_str
    
    def process(self, prompt_info: dict, **kwargs):
        prompt_template_key = kwargs.get("prompt_template_key", {})
        persona = prompt_template_key.get("persona", "")
        if persona in prompt_prefix_map:
            prompt_prefix = get_prompt_prefix(prompt_prefix_map[persona])
        else:
            prompt_prefix = " "
        
        prompt_template_key["prompt_prefix"] = prompt_prefix

        default_prompt_template_info = {"system": "", "human": ""}
        prompt_template_info = kwargs.get("prompt_template", default_prompt_template_info)

        default_user_prompt_template_info = {"system": "", "human": ""}
        user_prompt_template_info = kwargs.get(
            "user_prompt_template", default_user_prompt_template_info
        )

        system_prompt_template_str = self._get_prompt_template_str(
            user_prompt_template_info=user_prompt_template_info,
            prompt_template_info=prompt_template_info,
            prompt_template_key=prompt_template_key,
            prompt_type="system"
        )

        human_prompt_template_str = self._get_prompt_template_str(
            user_prompt_template_info=user_prompt_template_info,
            prompt_template_info=prompt_template_info,
            prompt_template_key=prompt_template_key,
            prompt_type="human"
        )

        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt_template_str),
                ("human", human_prompt_template_str)
            ]
        )

        prompt_info["prompt_template"] = prompt_template

        return prompt_info


class DocumentPromptTemplateProcessor(BasePromptProcessor):
    def process(self, prompt_info: dict, **kwargs):
        default_prompt_template_info = {"system": "", "human": ""}
        prompt_template_info = kwargs.get(
            "prompt_template", default_prompt_template_info
        )

        prompt_template_key = kwargs.get("prompte_template_key", {})

        if prompt_template_info["system"] in prompt_template_map:
            system_key = prompt_template_info["system"]
        else:
            system_key = "default_document_system_prompt_template"
        
        system_prompt_template_str = prompt_template_map[system_key].format(
            **prompt_template_key
        )

        if prompt_template_info["human"] in prompt_template_map:
            human_key = prompt_template_info["human"]
        else:
            human_key = "default_document_human_prompt_template"
        
        human_prompt_template_str = prompt_template_map[human_key].format(
            **prompt_template_key
        )

        user_system_message_template = kwargs.get("user_prompt_template", {}).get(
            "system", ""
        )

        if user_system_message_template:
            system_prompt_template_str = (
                user_system_message_template + system_prompt_template_str
            )
        
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt_template_str),
                ("human", human_prompt_template_str)

            ]
        )
        prompt_info["prompt_template"] = prompt_template

        print(f"==============================================")
        #print(f"DocumentPromptTemplateProcessor :: process() :: {prompt_info}")
        print(f"==============================================")

       

        return prompt_info



