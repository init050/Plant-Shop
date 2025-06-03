from django.apps import AppConfig


class ArticleModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'article_module'

    def ready(self):
        import article_module.signals