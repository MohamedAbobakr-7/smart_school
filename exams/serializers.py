from rest_framework import serializers
from smartSchool.messages import (
    MSG_OPTIONS_MUST_BE_LIST, MSG_MIN_OPTIONS,
    MSG_CORRECT_ANSWER_INDEX, MSG_GRADE_DUPLICATE,
    MSG_SCORE_EXCEEDS_TOTAL,
)
from .models import Exam, Question, Grade


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for Question model"""
    
    correct_answer_text = serializers.SerializerMethodField()
    options_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Question
        fields = [
            'id', 'exam', 'text', 'text_en', 'text_ar',
            'options', 'options_en', 'options_ar',
            'correct_answer',
            'correct_answer_text', 'options_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_correct_answer_text(self, obj):
        """Get the text of the correct answer"""
        return obj.get_correct_answer_text()
    
    def get_options_count(self, obj):
        """Get the number of options"""
        return len(obj.options) if obj.options else 0
    
    def validate(self, data):
        """Validate question data"""
        options = data.get('options', [])
        correct_answer = data.get('correct_answer')
        
        if not isinstance(options, list):
            raise serializers.ValidationError(str(MSG_OPTIONS_MUST_BE_LIST))
        
        if len(options) < 2:
            raise serializers.ValidationError(str(MSG_MIN_OPTIONS))
        
        if correct_answer is not None and correct_answer >= len(options):
            raise serializers.ValidationError(
                str(MSG_CORRECT_ANSWER_INDEX).format(index=correct_answer, count=len(options))
            )
        
        return data


class ExamSerializer(serializers.ModelSerializer):
    """Serializer for Exam model"""
    
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    subject_code = serializers.CharField(source='subject.code', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    teacher_id_display = serializers.CharField(source='teacher.teacher_id', read_only=True)
    exam_type_display = serializers.CharField(source='get_exam_type_display', read_only=True)
    questions_count = serializers.SerializerMethodField()
    grades_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Exam
        fields = [
            'id', 'name', 'name_en', 'name_ar',
            'exam_type', 'exam_type_display',
            'subject', 'subject_name', 'subject_code',
            'teacher', 'teacher_name', 'teacher_id_display',
            'duration', 'exam_date', 'class_id',
            'questions_count', 'grades_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_questions_count(self, obj):
        """Get the number of questions in this exam"""
        return obj.get_questions_count()
    
    def get_grades_count(self, obj):
        """Get the number of students who have taken this exam"""
        return obj.get_grades_count()


class ExamDetailSerializer(ExamSerializer):
    """Detailed serializer for Exam with questions"""
    
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta(ExamSerializer.Meta):
        fields = ExamSerializer.Meta.fields + ['questions']


class GradeSerializer(serializers.ModelSerializer):
    """Serializer for Grade model"""
    
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    exam_name = serializers.CharField(source='exam.name', read_only=True)
    subject_name = serializers.CharField(source='exam.subject.name', read_only=True)
    percentage = serializers.SerializerMethodField()
    grade_letter = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()
    
    class Meta:
        model = Grade
        fields = [
            'id', 'student', 'student_id', 'student_name',
            'exam', 'exam_name', 'subject_name',
            'score', 'percentage', 'grade_letter', 'total_questions',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_percentage(self, obj):
        """Calculate percentage score"""
        return round(obj.get_percentage(), 2)
    
    def get_grade_letter(self, obj):
        """Get letter grade"""
        return obj.get_grade_letter()
    
    def get_total_questions(self, obj):
        """Get total questions in the exam"""
        return obj.exam.get_questions_count()
    
    def validate(self, data):
        """Validate grade data"""
        student = data.get('student')
        exam = data.get('exam')
        score = data.get('score')
        
        # Check for duplicate grade (excluding current instance if updating)
        if student and exam:
            existing = Grade.objects.filter(student=student, exam=exam)
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise serializers.ValidationError(
                    str(MSG_GRADE_DUPLICATE)
                )
        
        # Validate score doesn't exceed total questions
        if exam and score is not None:
            total_questions = exam.get_questions_count()
            if total_questions > 0 and score > total_questions:
                raise serializers.ValidationError(
                    str(MSG_SCORE_EXCEEDS_TOTAL).format(score=score, total_questions=total_questions)
                )
        
        return data
