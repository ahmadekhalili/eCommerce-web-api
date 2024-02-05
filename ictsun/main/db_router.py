

class MongoRouter:
    allowed_models = []     # allowed_models is blank so not any collection (table) for creation

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if model_name in self.allowed_models:
            return db == 'mongo'
        if db == 'mongo':
            return False
        return None
