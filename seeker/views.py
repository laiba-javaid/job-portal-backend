from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from seeker import serializers
from seeker.models import SeekerProfile, Experience, Resume
from seeker.permissions import IsAdminOrOwner

class SeekerProfileViewSet(viewsets.ModelViewSet):
    queryset = SeekerProfile.objects.all()
    serializer_class = serializers.SeekerProfileSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['GET', 'PATCH'], permission_classes=[IsAuthenticated])
    def my_profile(self, request):
        obj, created = SeekerProfile.objects.get_or_create(user=request.user)
        if request.method == 'GET':
            serializer = self.get_serializer(obj)
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif request.method == 'PATCH':
            serializer = self.get_serializer(obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResumeViewSet(viewsets.ModelViewSet):
    queryset = Resume.objects.all()
    serializer_class = serializers.ResumeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwner]
    parser_classes = [MultiPartParser, FormParser]  # Add parsers for file upload
    
    def get_queryset(self):
        return Resume.objects.filter(seeker__user=self.request.user).order_by('-id')
    
    @action(detail=False, methods=['POST'], permission_classes=[IsAuthenticated])
    def upload(self, request):
        """
        Upload a resume file - accessible at /api/resume/upload/
        """
        if 'resume' not in request.FILES:
            return Response(
                {'error': 'No resume file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        resume_file = request.FILES['resume']
        
        # Validate file type
        allowed_extensions = ['.pdf', '.doc', '.docx']
        file_extension = resume_file.name.lower().split('.')[-1]
        if f'.{file_extension}' not in allowed_extensions:
            return Response(
                {'error': 'Invalid file type. Only PDF, DOC, and DOCX files are allowed.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size (10MB limit)
        max_size = 10 * 1024 * 1024
        if resume_file.size > max_size:
            return Response(
                {'error': 'File size too large. Maximum size is 10MB.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get or create seeker profile
            seeker_profile, created = SeekerProfile.objects.get_or_create(
                user=request.user
            )
            
            # Generate resume title from filename if not provided
            resume_title = request.data.get('resume_title')
            if not resume_title:
                resume_title = resume_file.name.rsplit('.', 1)[0]
            
            # Create Resume instance
            resume = Resume.objects.create(
                seeker=seeker_profile,
                resume_title=resume_title,
                resume=resume_file
            )
            
            # Return response data
            response_data = {
                'id': resume.id,
                'resume_title': resume.resume_title,
                'resume_url': resume.resume.url,
                'date_created': resume.date_created,
                'message': 'Resume uploaded successfully'
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Upload failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ExperienceViewSet(viewsets.ModelViewSet):
    queryset = Experience.objects.all()
    serializer_class = serializers.ExperienceSerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwner]
    
    def get_queryset(self):
        return Experience.objects.filter(seeker__user=self.request.user).order_by('-id')