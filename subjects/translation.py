from modeltranslation.translator import register, TranslationOptions
from .models import Subject, Material


@register(Subject)
class SubjectTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


@register(Material)
class MaterialTranslationOptions(TranslationOptions):
    fields = ('title', 'description')