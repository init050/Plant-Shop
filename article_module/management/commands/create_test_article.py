from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from article_module.models import Article
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a test article for debugging'

    def handle(self, *args, **options):
        # Get or create a test user
        user, created = User.objects.get_or_create(
            email='test@example.com',
            defaults={
                'username': 'testuser',
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(f'Created test user: {user.email}')
        
        # Create a test article
        article, created = Article.objects.get_or_create(
            title='Test Article - Plant Care Tips',
            defaults={
                'summary': 'This is a test article about plant care. Learn how to keep your plants healthy and thriving with these simple tips.',
                'content': '''
# Plant Care Tips

## Watering
Plants need regular watering, but not too much. Check the soil moisture before watering.

## Light
Most plants need bright, indirect light. Avoid direct sunlight which can burn leaves.

## Soil
Use well-draining soil that's appropriate for your plant type.

## Fertilizer
Feed your plants during the growing season with a balanced fertilizer.
                ''',
                'author': user,
                'status': Article.PUBLISHED,
                'publish_date': timezone.now(),
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created test article: "{article.title}"')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Test article already exists: "{article.title}"')
            )
        
        # Create another test article
        article2, created = Article.objects.get_or_create(
            title='Gardening for Beginners',
            defaults={
                'summary': 'A comprehensive guide for new gardeners. Start your gardening journey with confidence.',
                'content': '''
# Gardening for Beginners

## Getting Started
Choose easy-to-grow plants for your first garden. Herbs and vegetables are great choices.

## Tools You Need
- Trowel
- Watering can
- Pruning shears
- Garden gloves

## Location
Find a spot with good sunlight and access to water.
                ''',
                'author': user,
                'status': Article.PUBLISHED,
                'publish_date': timezone.now(),
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created test article: "{article2.title}"')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Test article already exists: "{article2.title}"')
            )
        
        # Show all articles
        all_articles = Article.objects.all()
        self.stdout.write(f'\nTotal articles in database: {all_articles.count()}')
        for article in all_articles:
            self.stdout.write(f'- {article.title} (Status: {article.status})')
