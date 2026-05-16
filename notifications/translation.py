from modeltranslation.translator import register, TranslationOptions
from .models import Notification


@register(Notification)
class NotificationTranslationOptions(TranslationOptions):
    fields = ('title', 'body')