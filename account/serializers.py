from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from company.models import Company
from seeker.models import SeekerProfile

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    # Company fields (optional during registration)
    company_title = serializers.CharField(max_length=150, required=False, allow_blank=True, write_only=True)
    company_location = serializers.CharField(max_length=150, required=False, allow_blank=True, write_only=True)
    company_description = serializers.CharField(required=False, allow_blank=True, write_only=True)
    company_website = serializers.URLField(required=False, allow_blank=True, write_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'role', 'first_name', 'last_name', 'get_full_name',
            'company_title', 'company_location', 'company_description', 'company_website'
        ]
        extra_kwargs = {'password': {'write_only': True}}
    
    def validate(self, attrs):
        # If role is company, require at least company title
        if attrs.get('role') == 'company':
            if not attrs.get('company_title'):
                raise serializers.ValidationError({
                    'company_title': 'Company title is required when registering as a company.'
                })
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        # Extract company-related fields
        company_data = {
            'title': validated_data.pop('company_title', ''),
            'location': validated_data.pop('company_location', ''),
            'description': validated_data.pop('company_description', ''),
            'website': validated_data.pop('company_website', None),
        }
        
        # Create the user
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        
        # Create profile based on role
        if user.role == 'company':
            # Use company title or fallback to user's full name
            company_title = company_data['title'] or f"{user.first_name} {user.last_name}"
            
            Company.objects.create(
                user=user,
                title=company_title,
                location=company_data['location'] or '',
                description=company_data['description'] or f"Welcome to {company_title}!",
                website=company_data['website'] if company_data['website'] else None,
                is_active=False  # Company needs to be activated later
            )
        
        elif user.role == 'job_seeker':
            # Create seeker profile automatically
            SeekerProfile.objects.create(
                user=user,
                # Add any default fields for seeker profile if needed
            )
        
        return user
