from rest_framework import serializers
from django.conf import settings
from django.utils import translation
from smartSchool.messages import MSG_CLASS_NAME_REQUIRED, MSG_CLASS_ALREADY_EXISTS
from .models import SchoolClass


class SchoolClassSerializer(serializers.ModelSerializer):
    display_name = serializers.ReadOnlyField()

    class Meta:
        model = SchoolClass
        fields = [
            'id', 'name', 'name_en', 'name_ar',
            'section', 'display_name',
            'description', 'description_en', 'description_ar',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'display_name', 'created_at', 'updated_at']
        extra_kwargs = {
            'name_en': {'required': False, 'allow_blank': True},
            'name_ar': {'required': False, 'allow_blank': True},
            'description_en': {'required': False, 'allow_blank': True},
            'description_ar': {'required': False, 'allow_blank': True},
        }

    def validate(self, data):
        name = data.get('name', getattr(self.instance, 'name', '')).strip()
        section = data.get('section', getattr(self.instance, 'section', '')).strip()
        if not name:
            raise serializers.ValidationError({'name': str(MSG_CLASS_NAME_REQUIRED)})
        # Uniqueness check excluding current instance on update
        qs = SchoolClass.objects.filter(name=name, section=section)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            label = f"{name} - {section}" if section else name
            raise serializers.ValidationError(
                str(MSG_CLASS_ALREADY_EXISTS).format(label=label)
            )
        data['name'] = name
        data['section'] = section

        # Sync the translation-proxy field values to the current language's
        # real DB columns.  Without this, Django's Model.__init__ overwrites
        # the descriptor-set value with the field default (None / '') because
        # the concrete field name (e.g. name_en) was not in kwargs — or it
        # was present but falsy (None / '') from DRF field-level validation.
        lang = translation.get_language() or settings.LANGUAGE_CODE
        name_lang_field = f'name_{lang}'
        desc_lang_field = f'description_{lang}'
        if name and not data.get(name_lang_field):
            data[name_lang_field] = name
        desc = data.get('description', getattr(self.instance, 'description', '')).strip()
        if desc and not data.get(desc_lang_field):
            data[desc_lang_field] = desc

        return data
