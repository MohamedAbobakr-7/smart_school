from modeltranslation.translator import register, TranslationOptions
from .models import Exam, Question


@register(Exam)
class ExamTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(Question)
class QuestionTranslationOptions(TranslationOptions):
    fields = ('text', 'options')