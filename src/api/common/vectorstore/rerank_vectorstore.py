from typing import Dict, Any, List, Optional

from langchain.chains import LLMChain
from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from langchain.pydantic_v1 import root_validator
from langchain.retrievers import EnsembleRetriever
from langchain.retrievers.multi_query import LineListOutputParser, DEFAULT_QUERY_PROMPT
from langchain_community.retrievers import BM25Retriever, TFIDFRetriever
from langchain.schema import BaseRetriever, Document
from langchain_core.runnables import RunnableConfig

from src.api.common.logging.Logger import log

class RerankRetriever(EnsembleRetriever):
    retrievers: List[BaseRetriever] = []
    query_gen_llm_chain: LLMChain = None
    base_retriever: BaseRetriever
    retrieving_mode: str = "precise"
    top_k: int = 20
    base_top_k: int = 50
    verbose: bool = True

    @root_validator(pre=True)
    def set_weights(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if not values.get("weights"):
            values["weights"] = [0.5, 0.5]
        return values
    
    def set_llm(self, llm):
        """
        Set llm and create a LLMChain to generate queries similar to user query
        """
        output_parser = LineListOutputParser()
        self.query_gen_llm_chain = LLMChain(
            llm=llm, prompt=DEFAULT_QUERY_PROMPT, output_parser=output_parser
        )
    
    def rank_fusion(self, query: str, run_manager: CallbackManagerForRetrieverRun, *, config: Optional[RunnableConfig] = None) -> List[Document]:
        """
        Get the relevant document for a given query
        """

        print(f"==============================================")
        print(f"RerankRetriever :: rank_fusion() :: query : {query}")
        print(f"==============================================")


        base_documents = self._get_base_relevant_documents(
            query=query, run_manager=run_manager
        )

        # print(f"==============================================")
        # print(f"RerankRetriever :: rank_fusion() :: base_documents : {base_documents}")
        # print(f"==============================================")


        log.info(f"base doc length = {len(base_documents)}")
        if len(base_documents) == 0:
            return base_documents
        
        bm25_retriever = BM25Retriever.from_documents(
            documents=base_documents, k=self.base_top_k
        )

        bm25_documents = bm25_retriever.get_relevant_documents(query)

        # print(f"==============================================")
        # print(f"RerankRetriever :: rank_fusion() :: bm25_documents : {bm25_documents}")
        # print(f"==============================================")


        log.info(f"bm25_documents length = {len(bm25_documents)}")

        tfidf_retriever = TFIDFRetriever.from_documents(
            documents=base_documents, k=self.base_top_k
        )

        tfidf_documents = tfidf_retriever.get_relevant_documents(query)

        retriever_docs = [
            bm25_documents,
            #tfidf_documents.
            base_documents
        ]

        fused_documents = self.weighted_reciprocal_rank(retriever_docs)

        # print(f"==============================================")
        # print(f"RerankRetriever :: rank_fusion() :: fused_documents 1 : {fused_documents}")
        # print(f"==============================================")


        fused_documents = fused_documents[: self.top_k]

        # print(f"==============================================")
        # print(f"RerankRetriever :: rank_fusion() :: fused_documents 2 : {fused_documents}")
        # print(f"==============================================")

        return fused_documents
    
    def _get_similar_queries(self, query:str, run_manager: CallbackManagerForRetrieverRun):
        response = self.query_gen_llm_chain(
            {"question": query}, callbacks=run_manager.get_child()
        )

        parser_key = "lines"
        queries = response.get("text", [])
        if self.verbose:
            log.info(f"Generated queries : {queries}")
        return queries
    
    def _get_base_relevant_documents(
            self, query:str, run_manager=CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """
        Generate base relevant documents upon user input
        """
        if self.retrieving_mode == "precise":
            queries = self._get_similar_queries(query, run_manager)
        
        else:
            queries = [query]
        
        documents_store_list = []
        for query in queries:
            documents_store_sub_list = (
                self.base_retriever.vectorstore.similarity_search_with_relevance_scores(
                    query, **self.base_retriever.search_kwargs
                )
            )
            documents_store_list.extend(documents_store_sub_list)
        
        unique_documents_score_dict = {
            (doc.page_content, tuple(sorted(doc.metadata.items()))): (doc, score)
            for doc, score in documents_store_list
        }

        unique_documents_scores = list(unique_documents_score_dict.values())
        unique_documents_scores_sorted = sorted(
            unique_documents_scores, key=lambda x: x[1], reverse=True
        ) 

        unique_documents = [
            doc for doc, _ in unique_documents_scores_sorted[: self.base_top_k]
        ]

        for i, (doc, score) in enumerate(
            unique_documents_scores_sorted[: self.base_top_k]
        ):
            unique_documents[i].metadata["embedding_score"] = score
            unique_documents[i].metadata["embedding_rank"] = f"{i+1}"
        
        return unique_documents

