"""
please define your own chain template in the dict
"""

chain_template = {
    "exact_answer_map_reduce_special_intention": {
        "history": ["BaseHistoryProcessor"],
        "retrieval_chunks": ["BaseChunksProcessor"],
        "prompt": ["BasePromptProcessor", "SpecificIntentionPromptProcessor"],
        "prompt_template": {
            "system": "default_document_system_prompt_template",
            "human": "default_document_human_prompt_template"
        },
        "special_intent": ["DocumentAnalysisIntent", "TranslateIntent"],
        "chain": {
            "class": "CombinedDocumentConversationChain",
            "qa_chain_type": "map_reduce"
        }
    },

    "exact_answer_stuff_special_intention": {
        "history": ["BaseHistoryProcessor"],
        "retrieval_chunks": ["BaseChunksProcessor"],
        "prompt": ["BasePromptProcessor", "SpecificIntentionPromptProcessor"],
        "prompt_template": {
            "system": "default_document_system_prompt_template",
            "human": "default_document_human_prompt_template"
        },
        "special_intent": ["DocumentAnalysisIntent", "TranslateIntent"],
        "chain": {
            "class": "CombinedDocumentConversationChain",
            "qa_chain_type": "stuff"
        }
    },

    "exact_answer_map_reduce": {
        "history": ["BaseHistoryProcessor"],
        "retrieval_chunks": ["BaseChunksProcessor"],
        "prompt": ["BasePromptProcessor"],
        "prompt_template": {
            "system": "default_document_system_prompt_template",
            "human": "default_document_human_prompt_template"
        },
        "special_intent": ["DocumentAnalysisIntent", "TranslateIntent"],
        "chain": {
            "class": "CombinedDocumentConversationChain",
            "qa_chain_type": "map_reduce"
        }
    },


    "non_exact_answer_special_intention": {
        "history": ["BaseHistoryProcessor"],
        "retrieval_chunks": ["BaseChunksProcessor"],
        "prompt": ["SpecificIntentionPromptProcessor", "DocumentPromptTemplateProcessor"],
        "prompt_template": {
            "system": "default_document_system_prompt_template",
            "human": "default_document_human_prompt_template"
        },
        "special_intent": ["DocumentAnalysisIntent", "TranslateIntent"],
        "chain": {
            "class": "RetrievalConversationChain"
        }
    },


    "non_exact_answer": {
        "history": ["BaseHistoryProcessor"],
        "retrieval_chunks": ["BaseChunksProcessor"],
        "prompt": ["DocumentPromptTemplateProcessor"],
        "prompt_template": {
            "system": "default_document_system_prompt_template",
            "human": "default_document_human_prompt_template"
        },
        "special_intent": ["DocumentAnalysisIntent", "TranslateIntent"],
        "chain": {
            "class": "RetrievalConversationChain"
        }
    },

    "prompt_conversation_chain": {
        "history": ["BaseHistoryProcessor"],
        "retrieval_chunks": [],
        "prompt": ["PromptTemplateProcessor"],
        "prompt_template": {
            "system": "default_system_prompt_template",
            "human": "default_human_prompt_template"
        },
        "special_intent": [],
        "chain": {
            "class": "BaseConversationChain"
        }
    }




}