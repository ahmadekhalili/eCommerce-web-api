

class MongoRouter:
    allowed_models = ['mproduct', 'test']

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if model_name in self.allowed_models:
            return db == 'mongo'
        if db == 'mongo':
            return False
        return None
