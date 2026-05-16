from rest_framework import serializers

from smartSchool.messages import MSG_WEEK_PARAMS_BOTH_OR_NONE, MSG_WEEK_END_AFTER_START
from .models import Report, WeeklyReport


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'


class WeeklyReportSerializer(serializers.ModelSerializer):
    pdf_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = WeeklyReport
        fields = [
            'id',
            'week_start',
            'week_end',
            'scope',
            'teacher',
            'status',
            'attendance_stats',
            'academic_stats',
            'exam_stats',
            'charts_payload',
            'insights',
            'comparison_prior_week',
            'error_message',
            'pdf_file',
            'pdf_url',
            'generated_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'status',
            'attendance_stats',
            'academic_stats',
            'exam_stats',
            'charts_payload',
            'insights',
            'comparison_prior_week',
            'error_message',
            'pdf_file',
            'generated_at',
            'created_at',
            'updated_at',
        ]

    def get_pdf_url(self, obj):
        if obj.pdf_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.pdf_file.url)
            return obj.pdf_file.url
        return None


class WeeklyReportGenerateSerializer(serializers.Serializer):
    week_start = serializers.DateField(required=False)
    week_end = serializers.DateField(required=False)
    scope = serializers.ChoiceField(
        choices=WeeklyReport.Scope.choices,
        default=WeeklyReport.Scope.TEACHER,
    )
    write_pdf = serializers.BooleanField(default=True)
    all_teachers = serializers.BooleanField(
        default=False,
        help_text="Admin only: generate school + every teacher for the window.",
    )

    def validate(self, attrs):
        ws = attrs.get('week_start')
        we = attrs.get('week_end')
        if (ws is None) ^ (we is None):
            raise serializers.ValidationError(
                str(MSG_WEEK_PARAMS_BOTH_OR_NONE)
            )
        if ws and we and we < ws:
            raise serializers.ValidationError(str(MSG_WEEK_END_AFTER_START))
        return attrs
