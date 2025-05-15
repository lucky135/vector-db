import json
import os
from dotenv import load_dotenv, find_dotenv
import boto3

from src.api.common.logging.Logger import log

def get_env_from_secret_manager(env):
    client = boto3.client("secretsmanager", region_name="ap-south-1")

def load_env_params():
    log.info("Loading env variables")
    load_dotenv(find_dotenv())
    env = os.getenv("PRSMGPT_ENV")
    if env!= "local":
        get_env_from_secret_manager(env)