from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from account.serializers import UserSerializer
from company.models import Company, Job, Application
from seeker.models import SeekerProfile
from seeker.serializers import SeekerProfileSerializer

class CompanySerializer(serializers.ModelSerializer):
    user = UserSerializer(required=False, read_only=True)
    
    # Add computed fields for better representation
    user_info = serializers.SerializerMethodField(read_only=True)
    total_jobs = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Company
        fields = "__all__"
        read_only_fields = ['user']  # Prevent user field modification
    
    def get_user_info(self, obj):
        """Return basic user information"""
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'full_name': obj.user.get_full_name(),
                'email': obj.user.email,
            }
        return None
    
    def get_total_jobs(self, obj):
        """Return total number of jobs posted by this company"""
        return obj.jobs.count()
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class JobSerializer(serializers.ModelSerializer):
    company = CompanySerializer(required=False, read_only=True)
    company_name = serializers.SerializerMethodField(read_only=True)
    applications_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Job
        fields = "__all__"
        read_only_fields = ['company']  # Prevent company field modification
    
    def get_company_name(self, obj):
        """Return company name for easier access"""
        return obj.company.title if obj.company else None
    
    def get_applications_count(self, obj):
        """Return number of applications for this job"""
        return obj.applications.count()
    
    def create(self, validated_data):
        user = self.context['request'].user
        try:
            company = Company.objects.get(user=user)
        except ObjectDoesNotExist:
            raise serializers.ValidationError("The user does not have an associated company.")
        
        if not company.is_active:
            raise PermissionDenied("The company approval is pending at the Admin.")
        
        validated_data['company'] = company
        return super().create(validated_data)

class ApplicationSerializer(serializers.ModelSerializer):
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.all())
    
    # Add computed fields for better representation
    job_title = serializers.SerializerMethodField(read_only=True)
    company_name = serializers.SerializerMethodField(read_only=True)
    applicant_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Application
        fields = "__all__"
        read_only_fields = ['applicant']
    
    def get_job_title(self, obj):
        """Return job title for easier access"""
        return obj.job.title if obj.job else None
    
    def get_company_name(self, obj):
        """Return company name for easier access"""
        return obj.job.company.title if obj.job and obj.job.company else None
    
    def get_applicant_name(self, obj):
        """Return applicant name for easier access"""
        return obj.applicant.user.get_full_name() if obj.applicant and obj.applicant.user else None
    
    def create(self, validated_data):
        try:
            validated_data['applicant'] = SeekerProfile.objects.get(user=self.context['request'].user)
        except SeekerProfile.DoesNotExist:
            raise serializers.ValidationError("The user does not have an associated seeker profile.")
        return super().create(validated_data)
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['job'] = JobSerializer(instance.job).data
        representation['applicant'] = SeekerProfileSerializer(instance.applicant).data
        return representation