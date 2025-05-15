import os
import re

import pypdf
import pandas as pd 
import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import urlparse, parse_qs, unquote_plus
from unstructured.partition.common import convert_office_doc
from unstructured.partition.docx import partition_docx
from unstructured.partition.pptx import partition_pptx
from unstructured.partition.xlsx import partition_xlsx

from langchain.docstore.document import Document
from langchain_community.document_loaders import (
    DataFrameLoader
)

from src.api.common.logging.Logger import log

def delete_file(filname):
    try:
        os.remove(filname)
        log.info(f"Deleted file : {filname}")
    except FileNotFoundError:
        log.error(f"File not found : {filname}")

def fix_text_problems(text: str):
    """
    Preprocess the text to fis common text problems

    Parameters:
    - text - Text string to process

    Retruns:
    Processed string
    """
    text = re.sub("\\n", " ", text)  # word combination in the next line
    text = re.sub("\s+[-]\s+", "", text) # word continuation in the next line
    return text

def extract_csv(file, filename):
    """
    Extract text from csv file

    Parameters:
    - file -  The file object
    - filename - The name of the file

    Returns: Extracted CSV content
    """
    try:
        log.info(f"Loafding csv file {filename}")
        df = pd.read_csv(file)
        df["file_name"] = filename
        loader = DataFrameLoader(df, page_content_column="file_name")

        csv_loader = loader.load()
        docs = []
        for i, row in enumerate(csv_loader):
            additional_metadata = {"source": filename, "page_number": f"Row-{i + 1}"}
            row.metadata.update(additional_metadata)
            docs.append(
                Document(
                    page_content="\n".join(
                        f"{k}: {v}" for k, v in row.metadata.items()
                    ),
                    metadata = row.metadata
                )
            )
    except Exception:
        raise Exception("[ERROR] - Unable to read file")
    return docs

#NEED TO USE TEXTRACT FOR BETTER RESULTS
def extract_pdf(file, filename):
    """
    Extract text from pdf file

    Parameters:
    - file -  The file object
    - filename - The name of the file

    Returns: Extracted pdf content
    """
    try:
        log.info(f"Loafding csv file {filename}")
        pdf_reader = pypdf.PdfReader(file)
        docs = [
            Document(
                page_content=page.extract_text(),
                metadata = {"source": filename, "page_number": f"Page-{i+1}"}
            )
            for i, page in enumerate(pdf_reader.pages)
        ]
    except Exception:
        raise Exception("[ERROR] - Unable to read file")
    return docs 


def extract_word(file, filename, extension: str):
    """
    Extract text from wrod file

    Parameters:
    - file -  The file object
    - filename - The name of the file
    - extension - File extension

    Returns: Extracted word content
    """
    try:
        log.info(f"Loafding csv file {filename}")
        if extension == "docx":
            elements = partition_docx(file=file, metadata_filename=filename)
        else:
            convert_office_doc(filename, "./", target_format="docx")
            docx_filename = os.path.join("./", f"{filename}x")
            elements = partition_docx(filename=docx_filename, metadata_filename=filename)
            delete_file(docx_filename)

        text = "\n\n".join([str(el) for el in elements])
        docs = [Document(page_content=text, metadata={"source": filename})]
    except Exception:
        raise Exception("[ERROR] - Unable to read file")
    return docs

def extract_txt(file, filename):
    """
    Extract text from txt file

    Parameters:
    - file -  The file object
    - filename - The name of the file

    Returns: Extracted txt content
    """
    try:
        log.info(f"Loafding csv file {filename}")
        text = str(file.read())
        docs = [Document(page_content=text, metadata={"source": filename})]
    except Exception:
        raise Exception("[ERROR] - Unable to read file")
    return docs


def extract_ppt(file, filename, extension: str):
    """
    Extract text from ppt file

    Parameters:
    - file -  The file object
    - filename - The name of the file
    - extension - File extension

    Returns: Extracted ppt content
    """
    try:
        log.info(f"Loafding csv file {filename}")
        if extension == "pptx":
            elements = partition_pptx(file=file, metadata_filename=filename)
        else:
            convert_office_doc(filename, "./", target_format="pptx")
            pptx_filename = os.path.join("./", f"{filename}x")
            elements = partition_pptx(filename=pptx_filename, metadata_filename=filename)
            delete_file(pptx_filename)

        text = "\n\n".join([str(el) for el in elements])
        docs = [
            Document(
                page_content=page, 
                metadata={"source": filename, "page_number": f"Page-{i+1}"}
            )
            for i, page in enumerate(text.split("\n\n\n"))
        ]
    except Exception:
        raise Exception("[ERROR] - Unable to read file")
    return docs


def extract_excel(file, filename, extension: str, require_rows_processing):
    """
    Extract text from excel file

    Parameters:
    - file -  The file object
    - filename - The name of the file
    - extension - File extension

    Returns: Extracted excel content
    """
    try:
        log.info(f"Loading csv file {filename}")
        if extension == "xlsx":
            if require_rows_processing:
                elements = []
                df = pd.read_excel(file)
                # Assuming the Excel has the following columns: Description, HSN Code, CGST, SGST, GST
                for index, row in df.iterrows():
                    # Initialize an empty string to store the concatenated row data
                    row_text = ""

                    for column in df.columns:
                        # Get the column value, and replace it with "-" if it's null or empty
                        column_value = row[column] if pd.notnull(row[column]) and str(row[column]).strip() != "" else "-"
            
                        # Concatenate the column name and the value to the row_text string
                        row_text += f"{column}: {column_value} | "

                    # Remove the last " | " from the concatenated string
                    row_text = row_text.rstrip(" | ")

                    # Skip rows where the concatenated text is empty (i.e., all values were empty or null)
                    if not row_text.strip():
                        continue
                    else:
                        elements.append(row_text)
            else:
                elements = partition_xlsx(file=file, metadata_filename=filename)
        else:
            convert_office_doc(filename, "./", target_format="docx")
            xlsx_filename = os.path.join("./", f"{filename}x")
            elements = partition_xlsx(filename=xlsx_filename, metadata_filename=filename)
            delete_file(xlsx_filename)

        docs = [
            Document(
                page_content=str(element), 
                metadata={"source": filename, "page_number": f"Page-{i+1}"}
            )
            for i, element in enumerate(elements)
        ]
    except Exception:
        raise Exception("[ERROR] - Unable to read file")
    return docs

def load(file, filename:str, require_rows_processing:bool):
    """
    Extract text from pdf/csv/word/ppt file

    Parameters:
    - file -  The file object
    - filename - The name of the file

    Returns Extracted file content
    """

    #Get the extension of file
    extension = filename.split(".")[-1]
    if extension == "pdf":
        docs = extract_pdf(file, filename)
    elif extension in ["docx", "doc"]:
        docs = extract_word(file, filename, extension)
    elif extension == "csv":
        docs = extract_csv(file, filename)
    elif extension in ["ppt", "pptx"]:
        docs = extract_ppt(file, filename, extension)
    elif extension in ["xlsx", "xls"]:
        docs = extract_excel(file, filename, extension, require_rows_processing)
    elif extension == "txt":
        docs = extract_txt(file, filename)
    else:
        raise ValueError(f"Unsupported file extension: {extension}")
    
    for doc in docs:
        doc.page_content = fix_text_problems(doc.page_content)

    output = {"docs": docs, "filename": filename}
    log.info(f"File {filename} load successfully")
    return output