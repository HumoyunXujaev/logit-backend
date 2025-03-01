from django.apps import AppConfig

class CargoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cargo'
    
    def ready(self):
        import cargo.signals  # Import signals when app is ready
