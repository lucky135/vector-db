"""
@author - Krishna Raghav
@copyright - Vector Softwares
"""

from django.db import models


class RAF(models.Model):
    sensitive_key = models.CharField(max_length=256)
    sensitive_value = models.TextField()
    additional_info = models.TextField(default="", blank=False, null=False)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)


class File_Metadata(models.Model):
    file_name = models.TextField()
    chunk_number = models.IntegerField(null=False, default=0)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)


class Prompt_Library(models.Model):
    name = models.CharField(max_length=256)
    prompt_type = models.CharField(max_length=256)
    description = models.TextField()
    persona = models.CharField(max_length=256)
    persona_base_prompt = models.TextField()
    output_format_type = models.TextField()
    output_format_prompt = models.TextField()
    prompt_text = models.TextField()
    status = models.CharField(max_length=256)
    created_date = models.DateField(auto_now_add=True)
    last_modified_date = models.DateField(auto_now_add=True)
