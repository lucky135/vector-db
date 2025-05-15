from os import getenv
import time
import numpy as np 

from langchain_postgres.vectorstores import PGVector
from sqlalchemy import select, delete

from src.api.common.logging.Logger import log


def get_pgvector_setting():
    """
    Retrieves the Postgres vector store settings from the env variables and returns the connection string

    parameters: None

    Returns:
    str: The Postgres connection string
    """

    username = getenv("PGVECTOR_USER")
    database = getenv("PGVECTOR_DB")
    password = getenv("PGVECTOR_PASSWORD")
    host = getenv("PGVECTOR_HOST")
    port = getenv("PGVECTOR_PORT")

    #connection string
    conn = f"postgresql+psycopg://{username}:{password}@{host}:{port}/{database}"
    return conn

class PgVectorStore(object):
    def __init__(self, embeddings, collection_name, **kwargs):
        """
        Initializes the PgVectorStore object

        Parameters:
         - embeddings - The embeddings to store in vector store
         - collection_name - The name of the collection where the emdeddings will be stored
         - **kwargs - Additonal keyword arguments.

         Returns:
         None
        """
        self.embeddings = embeddings
        self.collection_name = collection_name
        self.connection = get_pgvector_setting()
        self.use_jsonb = kwargs.get("usejsonb", True)
        self.vectorstore = self.__get_vectorstore(embeddings, collection_name, self.connection)

    
    def __get_vectorstore(self, emdeddings, collection_name, connection):
        """
        Creates a PGVector object with the provided parameters and returns it.

        Parameters:
         - embeddings - The embeddings to store in vector store
         - collection_name - The name of the collection where the emdeddings will be stored
         - connection - The postGres connection object

         Returns:
         PGVector: The PGVector object representing the vector store
        """

        return PGVector(
            collection_name=collection_name,
            embeddings=emdeddings,
            connection=connection,
            use_jsonb=self.use_jsonb
        )
    
    def get_collection_count(self):
        """
        Retrieves the count of documents in the collection

        Returns:
        int: The count of the documents in the collection
        """

        if self.vectorstore is None:
            log.info("Found None vector store in function get_collection_count()!!!")
            return 0

        with self.vectorstore._make_sync_session() as session:
            coll = self.vectorstore.get_collection(session)
            print(f"==============================================")
            print(f"Executing Vector Impl :: collection_count() :: coll : {coll.uuid}")
            print(f"==============================================")

            stmt = select(self.vectorstore.EmbeddingStore.id).where(
                self.vectorstore.EmbeddingStore.collection_id == coll.uuid
            )
            res = session.execute(stmt)
            return len(res.fetchall())
        
    def add_documents(self, documents):
        """
        Add documents to the vector store.

        Parameters:
        - documents: The documents to add.
        - file_name: The name of the file the documents belong to

        Return:
        None
        """

        if self.vectorstore is None:
            log.info("Found None vector store in function get_collection_count()!!!")
            return

        try:
            print(f"========== collection_name :: {self.vectorstore.collection_name}")
            self.vectorstore.add_documents(documents)
            log.info("Documents added successfully")
        except Exception as e:
            log.error(f"Error adding document: {str(e)}")
    

    def clear_collection(self):
        """
        Clears all documents in the collection

        Returns:
        None
        """
        try:
            with self.vectorstore._make_sync_session as session:
                coll = self.vectorstore.get_collection(session)
                stmt = delete(self.vectorstore.EmbeddingStore).where(
                    self.vectorstore.EmbeddingStore.collection_id == coll.uuid
                )
                session.execute(stmt)
                session.delete(coll)
                session.commit()
                log.info("Collection cleaned successfully")
                self.vectorstore = None
        except Exception as e:
            log.error(f"Error while deleting all documents: {str(e)}")
    

    def delete_documents(self, file_name):
        """
        Deletes documents with a specific file name from the collection.

        Parameters:
        - file_name: The name of the file to delete document from

        Returns: None
        """

        try:
            with self.vectorstore._make_sync_session as session:
                coll = self.vectorstore.get_collection(session)
                stmt = delete(self.vectorstore.EmbeddingStore).where(
                    self.vectorstore.EmbeddingStore.cmetadata["source"].astext == file_name,
                    self.vectorstore.EmbeddingStore.collection_id == coll.uuid
                )
                session.execute(stmt)
                session.commit()
                log.info("Collection cleaned successfully")
                self.vectorstore = None
        except Exception as e:
            log.error(f"Error while deleting all documents: {str(e)}")

    def get_texts_from_documents(self, file_name):
        """
        Retrieves texts from documents with a specific file name.

        Parameter:
        - file_name: The name of the file to retrieve texts from

        Returns:
        - documents: A list of retrieved documents
        - embeddings: A list of retrieved embeddings
        - metadata: A list of retrieved metadata.
        """

        if self.vectorstore is None:
            log.info("Found None vector store in function get_collection_count()!!!")
            return [], [], []
        
        try:
            with self.vectorstore._make_sync_session as session:
                coll = self.vectorstore.get_collection(session)
                stmt = select(
                    self.vectorstore.EmbeddingStore.embeddings,
                    self.vectorstore.EmbeddingStore.document,
                    self.vectorstore.EmbeddingStore.cmetadata
                ).where(
                    self.vectorstore.EmbeddingStore.cmetadata["source"].astext == file_name,
                    self.vectorstore.EmbeddingStore.collection_id == coll.uuid
                )

                results = session.execute(stmt).fetchall()
                embeddings, documents, metadatas = [], [], []

                for e, d, m in results:
                    embeddings.append(e)
                    documents.append(d)
                    metadatas.append(m)
                return documents, embeddings, metadatas
        except Exception as e:
            log.error(f"Error getting texts: {str(e)}")
    

    def _get_search_kwargs(self, retriever_threshold, file_name_list: list = None, k=None):
        """
        Constructs the search kwargs based on the provided parameters

        Parameters:
        - retriever_threshold: The threshold for retriever scores.
        - file_name_list: A list of file names to filter the search results
        - k: The number of search results to retrieve

        Returns:
        - search_kwargs: A disctionary containing the constrcuted search kwargs
        """

        search_kwargs = {"score_threshold": retriever_threshold}

        if len(file_name_list) > 0:
            search_kwargs["filter"] = {"source": {"$in": file_name_list}}
        
        if k is not None:
            search_kwargs["k"] = k
        
        return search_kwargs
    
    def get_retriever(self, **kwargs):
        retriever_threshold = kwargs.get("retriever_threshold", 0.7)
        file_name_list = kwargs.get("file_name_list", [])
        k = kwargs.get("k")

        search_kwargs = self._get_search_kwargs(
            retriever_threshold, file_name_list, k=k
        )
        log.info(f"search_kwargs = {search_kwargs}")

        # cretae a retriever using the vectorstore with search type as "simialrity_score_threshold"
        # and search kwargs as the previously obtained search kwargs

        retriever = self.vectorstore.as_retriever(
            search_type="similarity_score_threshold", search_kwargs=search_kwargs
        )
        return retriever


    def persist(self):
        pass


class VectorStoreFactory:
    @staticmethod
    def create(vector_store_type: str, emdeddings, collection_name, **kwargs):
        vector_store_map = {"pgvector": PgVectorStore}
        if vector_store_type in vector_store_map:
            return vector_store_map[vector_store_type](
                emdeddings, collection_name, **kwargs
            )
        else:
            raise ValueError(f"Vector database {vector_store_type} is not supported")