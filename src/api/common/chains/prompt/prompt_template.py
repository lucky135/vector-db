default_prompt_template = """
Your are an AI assistant that helps people find information.
If you see any link to a webpage or website in the question, then ignore it.

{{prompt_prefix}}

Reply back in english language.
"""

default_document_system_prompt_temolate = """
Only use the Context provided to answer the Question below.
-----------------

Context: {{context}}

------------------
"""

default_document_human_prompt_template = """
{{input}}
Reply back in english language.
"""

prompt_template_map = {
    "default_system_prompt_template": default_prompt_template,
    "default_human_prompt_template": "{{input}}",
    "default_document_system_prompt_template": default_document_system_prompt_temolate,
    "default_document_human_prompt_template": default_document_human_prompt_template
}