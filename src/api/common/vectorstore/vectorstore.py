from os import getenv

from langchain.retrievers.multi_query import MultiQueryRetriever
from src.api.common.logging.Logger import log 
from src.api.common.database.store_handler import store_handler
from src.api.common.vectorstore.vectorstore_impl import VectorStoreFactory
from src.api.completion.impl.embedding_model_wrapper import create_embeddings_model
from src.api.common.vectorstore.rerank_vectorstore import RerankRetriever

class VectorStoreWrapper:
    def __init__( self, collection_name, retriever_type="default", **kwargs):
        self.vector_store_type = getenv("VECTORSTORE_TYPE")
        log.info(f"VectorStore type : {self.vector_store_type}")
    
        self.embeddings_model = create_embeddings_model(
            openai_api_key=kwargs.get("openai_api_key"),
            openai_api_base=kwargs.get("openai_api_base"),
            openai_api_version=kwargs.get("openai_api_version")
        )
        self.collection_name = collection_name
        print(f"embeddings_model :: {self.embeddings_model}")
        print(f"collection_name :: {self.collection_name}")
        self.vectorstore = self._get_vectorstore(collection_name=self.collection_name)
        self.retriever_type = retriever_type

    
    def _get_vectorstore(self, collection_name):
        """
        Returns vectorstore
        """
        vectorestore = VectorStoreFactory.create(
            vector_store_type=self.vector_store_type,
            emdeddings=self.embeddings_model,
            collection_name=collection_name,
        )

        return vectorestore
    
    def save_embeddings(self, file_name, documents):
        """
        Save embeddings and file metadata for single file
        """

        batch_size = 500

        file_instance = store_handler.get(
            model_name="File_Metadata", file_name=file_name
        )

        if file_instance != "":
            raise ValueError(f"File {file_name} already exists")
        
        else:
            print("============ Using collection:", self.vectorstore.collection_name)

            # Step 1: Batch the documents for insertion into the vector store
            document_batches = self.batch_documents(documents, batch_size)

            # Step 3: Insert the batches into the vector store
            for batch in document_batches:
                self.vectorstore.add_documents(documents=batch)

            #self.vectorstore.add_documents(documents=documents)
            self.vectorstore.persist()

            log.info(f"Embeddings for {file_name} of collection {self.collection_name} are successfully saved.")

            chunk_number = len(documents)
            file_instance = store_handler.save(
                model_name="File_Metadata",
                file_name=file_name,
                chunk_number=chunk_number
            )

            log.info(f"File Metadata is saved successfully")

            file_collection_count = len(documents)
            log.info(f"Collection count for {file_name} = {file_collection_count}")
    

    def delete_file(self, file_name: str) -> str:
        file_instance = store_handler.get(
            model_name="File_Metadata", file_name=file_name
        )

        if file_instance != "":
            raise ValueError(f"File {file_name} for user {self.user_id} already exists")
        
        else:
            vectorstore_count = self.vectorstore.get_collection_count()
            if vectorstore_count > 0:
                self.vectorstore.delete_documents(file_name)
                self.vectorstore.persist()

                log.info(f"File {file_name} is deleted successfully.") 

                store_handler.delete(
                    model_name="File_Metadata",
                    file_name=file_name
                )
            
                return "[SUCCESS]: Delete Success"
            else:
                log.info(f"No embeddings found for file {file_name}")
                return "[ERROR]: File embeddings does not exists"
    

    def get_total_collection_count(self):
        """
        Return the collection count for every file
        """
        return self.vectorstore.get_collection_count()
    
    
    def get_text_from_document(self, file_name=None):
        """
        Get all the texts from documents in vector store
        """
        documents, embeddings, metadata = self.vectorstore.get_texts_from_documents(file_name)
        return documents, embeddings, metadata
    

    def get_retrieve(self, file_name_list: list, retriever_threshold, llm):
        """
        Get retriever from vector store
        """
        collection_count = self.vectorstore.get_collection_count()

        # print(f"==============================================")
        # print(f"Executing Vector Wrapper :: get_retrieve() :: collection_count : {collection_count}")
        # print(f"==============================================")

        # print(f"==============================================")
        # print(f"Executing Vector Wrapper :: get_retrieve() :: retriever_threshold : {retriever_threshold}")
        # print(f"==============================================")

        if collection_count>0:
            if self.retriever_type in ["precise", "effective"]:
                base_retriever = self.vectorstore.get_retriever(
                    retriever_threshold=retriever_threshold,
                    file_name_list=file_name_list,
                    k=20
                )
                retriever = RerankRetriever(base_retriever=base_retriever, retrieving_mode=self.retriever_type)
                retriever.set_llm(llm)
            else: # default type
                base_retriever = self.vectorstore.get_retriever(
                    retriever_threshold=retriever_threshold,
                    file_name_list=file_name_list
                )

                retriever = MultiQueryRetriever.from_llm(retriever=base_retriever, llm=llm)
            
            log.info(f"retriever type = {type(retriever)}")

            return retriever
        else:
            return None
    

    def batch_documents(self, documents, batch_size: int = 500):
        """Split the documents into smaller batches."""
        return [documents[i:i + batch_size] for i in range(0, len(documents), batch_size)]
