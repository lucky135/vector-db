from abc import abstractmethod
from typing import List

from langchain.schema import Document
from langchain_community.document_transformers import LongContextReorder

from src.api.common.logging.Logger import log
from src.api.common.utils.embedding_utils import get_num_tokens_from_string

class BaseChunksProcessor(object):
    def __init__(self):
        pass
    
    @abstractmethod
    def process(self, chunks: List[Document], prompt:str, **kwargs) -> List[Document]:
        return chunks

class RelevantChunksProcessor(BaseChunksProcessor):
    def process(self, chunks: List[Document], prompt: str, **kwargs) -> List[Document]:
        print(f"RelevantChunksProcessor process method")
        reordering = LongContextReorder()
        reordered_chunks = reordering.transform_documents(chunks)
        return reordered_chunks
    
class SummaryChunksProcessor(BaseChunksProcessor):
    def process(self, chunks: List[Document], prompt:str, **kwargs) -> List[Document]:
        print(f"SummaryChunksProcessor process method")
        return chunks

class TruncationChunksProcessor(BaseChunksProcessor):
    def process(self, chunks: List[Document], prompt:str, **kwargs) -> List[Document]:
        print(f"TruncationChunksProcessor process method")
        truncation_token_count = kwargs.get("truncation_token_count", 6000)

        index=0
        token_count=0
        for document in chunks:
            current_token_count = get_num_tokens_from_string(document.page_content)

            if index == 0:
                pass
            elif (current_token_count + token_count) > truncation_token_count:
                break

            index += 1
            token_count += current_token_count
        
        return chunks[:index]

class MergeChunksProcessor(BaseChunksProcessor):
    def process(self, chunks: List[Document], prompt:str, **kwargs) -> List[Document]:
        print(f"MergeChunksProcessor process method")
        merging_token_count = kwargs.get("merging_token_count", 4000)

        output_chunks = []
        last = 0
        token_count = 0
        for current, document in enumerate(chunks):
            current_token_count = get_num_tokens_from_string(document.page_content)
            if (current_token_count + token_count) > merging_token_count:
                if current == last:
                    merged_doc = chunks[last]
                    last = current + 1
                    token_count = 0
                
                else:
                    text_list = [chunks[i].page_content for i in range(last, current)]
                    merged_doc = Document(
                        page_content="\n".join(text_list),
                        metadata = chunks[last].metadata
                    )
                    last = current
                    token_count = current_token_count

                output_chunks.append(merged_doc)
            
            else:
                token_count += current_token_count
            
            if current == len(chunks) - 1 and last <= current:
                text_list = [chunks[i].page_content for i in range(last, current + 1)]
                merged_doc = Document(
                    page_content="\n".join(text_list), metadata=chunks[last].metadata
                )
                output_chunks.append(merged_doc)

        log.info(f"chunk length is {len(output_chunks)}")

        return output_chunks
