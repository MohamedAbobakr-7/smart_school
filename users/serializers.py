from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer that includes user role in token claims"""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['role'] = user.role
        token['username'] = user.username
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        
        return token

    def validate(self, attrs):
        # Students may sign in with school `student_id` instead of User.username.
        username_field = self.username_field
        raw = (attrs.get(username_field) or '').strip()
        if raw and not User.objects.filter(**{username_field: raw}).exists():
            from students.models import Student

            student = (
                Student.objects.filter(student_id__iexact=raw)
                .exclude(student_id__isnull=True)
                .exclude(student_id='')
                .select_related('user')
                .first()
            )
            if student and student.user.is_active and student.user.is_student():
                attrs = {**attrs, username_field: student.user.get_username()}

        data = super().validate(attrs)

        user_payload = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role,
            'role_display': self.user.get_role_display(),
        }
        profile = getattr(self.user, 'student_profile', None)
        if profile is not None and profile.student_id:
            user_payload['student_id'] = profile.student_id
        # Include student photo URL so the frontend sidebar/avatar can display it
        if profile is not None and profile.photo:
            request = self.context.get('request')
            if request:
                user_payload['photo_url'] = request.build_absolute_uri(profile.photo.url)
            else:
                user_payload['photo_url'] = profile.photo.url
        data['user'] = user_payload

        return data


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'role_display', 'phone_number', 'address',
            'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'last_login', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }

    def create(self, validated_data):
        """Create a new user with password"""
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        """Update user, handling password separately"""
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users with password"""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'first_name', 'last_name',
            'role', 'phone_number', 'address'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for viewing and updating the current user's profile."""
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    # Role-specific nested read-only fields
    student_profile = serializers.SerializerMethodField()
    teacher_profile = serializers.SerializerMethodField()
    parent_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'role_display', 'phone_number', 'address',
            'is_active', 'date_joined', 'created_at', 'updated_at',
            'student_profile', 'teacher_profile', 'parent_profile',
        ]
        read_only_fields = [
            'id', 'username', 'role', 'role_display', 'is_active',
            'date_joined', 'created_at', 'updated_at',
            'student_profile', 'teacher_profile', 'parent_profile',
        ]

    def get_student_profile(self, obj):
        profile = getattr(obj, 'student_profile', None)
        if profile is None:
            return None
        # Build absolute photo URL if a photo exists
        photo_url = None
        if profile.photo:
            request = self.context.get('request')
            if request:
                photo_url = request.build_absolute_uri(profile.photo.url)
            else:
                photo_url = profile.photo.url
        return {
            'student_id': profile.student_id,
            'date_of_birth': profile.date_of_birth,
            'class_level': profile.class_level,
            'class_id': profile.class_id,
            'school_class_display': getattr(profile.school_class, 'display_name', None) if profile.school_class else None,
            'face_registered': profile.face_registered,
            'photo_url': photo_url,
        }

    def get_teacher_profile(self, obj):
        profile = getattr(obj, 'teacher_profile', None)
        if profile is None:
            return None
        return {
            'teacher_id': profile.teacher_id,
            'department': profile.department,
            'specialization': profile.specialization,
            'hire_date': profile.hire_date,
        }

    def get_parent_profile(self, obj):
        profile = getattr(obj, 'parent_profile', None)
        if profile is None:
            return None
        return {
            'parent_id': profile.parent_id,
            'occupation': profile.occupation,
            'relationship': profile.relationship,
            'children_count': profile.get_children_count(),
        }
