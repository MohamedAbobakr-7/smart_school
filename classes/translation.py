from modeltranslation.translator import register, TranslationOptions
from .models import SchoolClass


@register(SchoolClass)
class SchoolClassTranslationOptions(TranslationOptions):
    fields = ('name', 'description')