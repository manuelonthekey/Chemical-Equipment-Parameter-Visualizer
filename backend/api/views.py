import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from .models import EquipmentDataset
from .serializers import EquipmentDatasetSerializer, RegisterSerializer, UserSerializer

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomLoginView(ObtainAuthToken):
    permission_classes = [permissions.AllowAny]
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })

def analyze_dataset(dataset):
    """
    Helper function to process the CSV and return statistics.
    """
    try:
        # Read the CSV file path
        df = pd.read_csv(dataset.file.path)
        
        # Clean column names (strip whitespace)
        df.columns = [c.strip() for c in df.columns]
        
        # Check if required columns exist (Basic validation)
        required_columns = ['Equipment Name', 'Type', 'Flowrate', 'Pressure', 'Temperature']
        if not all(col in df.columns for col in required_columns):
             return None, f"CSV missing required columns: {required_columns}"

        # Calculate Summary Statistics
        stats = {
            "file_id": dataset.id,
            "uploaded_at": dataset.uploaded_at,
            "total_count": len(df),
            "averages": {
                "flowrate": round(df['Flowrate'].mean(), 2),
                "pressure": round(df['Pressure'].mean(), 2),
                "temperature": round(df['Temperature'].mean(), 2),
            },
            "type_distribution": df['Type'].value_counts().to_dict(),
            "preview": df.head(10).to_dict(orient='records'),
            "records": df[['Equipment Name','Type','Flowrate','Pressure','Temperature']].to_dict(orient='records')
        }
        return stats, None
    except Exception as e:
        return None, str(e)

class UploadAndAnalyzeView(APIView):
    # Allow file uploads via multipart/form-data
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        file_serializer = EquipmentDatasetSerializer(data=request.data)
        
        if file_serializer.is_valid():
            # 1. Save the file to the database (History Management), linked to user
            dataset = file_serializer.save(user=request.user)
            
            # 2. Maintain only last 10 entries for THIS user
            # Get all IDs ordered by upload time (descending)
            ids = list(EquipmentDataset.objects.filter(user=request.user).values_list('id', flat=True).order_by('-uploaded_at'))
            if len(ids) > 10:
                # Delete older records
                EquipmentDataset.objects.filter(user=request.user).exclude(id__in=ids[:10]).delete()

            # 3. Process the CSV using Pandas
            stats, error = analyze_dataset(dataset)
            
            if error:
                dataset.delete()
                return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(stats, status=status.HTTP_201_CREATED)
        
        else:
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class HistoryView(APIView):
    """
    Returns the list of the last 10 uploaded datasets for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        datasets = EquipmentDataset.objects.filter(user=request.user).order_by('-uploaded_at')[:10]
        serializer = EquipmentDatasetSerializer(datasets, many=True)
        return Response(serializer.data)

class RetrieveAnalysisView(APIView):
    """
    Returns the analysis for a specific history item.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            dataset = EquipmentDataset.objects.get(pk=pk, user=request.user)
            stats, error = analyze_dataset(dataset)
            if error:
                return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)
            return Response(stats)
        except EquipmentDataset.DoesNotExist:
            return Response({"error": "Dataset not found"}, status=status.HTTP_404_NOT_FOUND)
