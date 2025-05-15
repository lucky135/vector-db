from django.apps import apps
from src.api.common.logging.Logger import log

class DBStoreHandler:
    def __init__(self, model_mapping):
        self.model_mapping = model_mapping

    def save(self, model_name, **arritbutes):
        if model_name not in self.model_mapping:
            return ValueError(f"Unknown model name : {model_name}")

        model_class = self.model_mapping[model_name]
        instance = model_class(**arritbutes)
        instance.save()

        return instance
    
    def get(self, model_name, **filters):
        if model_name not in self.model_mapping:
            return ValueError(f"Unknown model name : {model_name}")

        model_class = self.model_mapping[model_name]
        try:
            instance = model_class.objects.get(**filters)
        except Exception as e:
            return ""
        return instance
    
    def get_all(self, model_name, **filters):
        if model_name not in self.model_mapping:
            return ValueError(f"Unknown model name : {model_name}")

        model_class = self.model_mapping[model_name]
        response = model_class.objects.filter(**filters)
        return response
    
    def update(self, model_name, instance, **attributes):
        if model_name not in self.model_mapping:
            return ValueError(f"Unknown model name : {model_name}")
        
        for key, value in attributes.items():
            setattr(instance, key, value)
        
        instance.save()
        return instance
    
    def delete(self, model_name, **filters):
        if model_name not in self.model_mapping:
            return ValueError(f"Unknown model name : {model_name}")
        
        model_class = self.model_mapping[model_name]
        instance = model_class.objects.filter(**filters)
        instance.delete()

        return instance
    
    def delete_all(self, model_name, **filters):
        if model_name not in self.model_mapping:
            return ValueError(f"Unknown model name : {model_name}")
        
        model_class = self.model_mapping[model_name]
        queryset = model_class.objects.filter(**filters)
        queryset.all().delete()

        return queryset
    
    
def generate_model_mapping(app_name):
    app_config = apps.get_app_config(app_name)
    model_mapping = {model.__name__: model for model in app_config.get_models()}
    return model_mapping
    
MODEL_MAPPING = generate_model_mapping("api")

store_handler = DBStoreHandler(MODEL_MAPPING)