import os
import pandas as pd
import io
from datetime import datetime
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from .models import EquipmentDataset
from .serializers import EquipmentDatasetSerializer, RegisterSerializer, UserSerializer

REQUIRED_COLUMNS = ['Equipment Name', 'Type', 'Flowrate', 'Pressure', 'Temperature']

def normalize_dataframe(df):
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    for col in ['Flowrate', 'Pressure', 'Temperature']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def compute_stats_from_df(df, dataset_id=None, uploaded_at=None):
    df = normalize_dataframe(df)

    if not all(col in df.columns for col in REQUIRED_COLUMNS):
        return None, f"CSV missing required columns: {REQUIRED_COLUMNS}"

    stats = {
        "total_count": len(df),
        "averages": {
            "flowrate": round(df['Flowrate'].mean(), 2),
            "pressure": round(df['Pressure'].mean(), 2),
            "temperature": round(df['Temperature'].mean(), 2),
        },
        "type_distribution": df['Type'].value_counts().to_dict(),
        "preview": df.head(10).to_dict(orient='records'),
        "records": df[REQUIRED_COLUMNS].to_dict(orient='records')
    }
    if dataset_id is not None:
        stats["file_id"] = dataset_id
    if uploaded_at is not None:
        stats["uploaded_at"] = uploaded_at
    return stats, None

def render_avg_chart(averages):
    labels = ["Flowrate", "Pressure", "Temperature"]
    values = [
        averages.get("flowrate", 0),
        averages.get("pressure", 0),
        averages.get("temperature", 0),
    ]
    fig, ax = plt.subplots(figsize=(4.5, 2.6), dpi=130)
    colors = ["#4BC0C0", "#36A2EB", "#FF6384"]
    ax.bar(labels, values, color=colors)
    ax.set_ylabel("Average")
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight", transparent=True)
    plt.close(fig)
    buffer.seek(0)
    return buffer

def render_type_chart(type_distribution):
    labels = list(type_distribution.keys())
    values = list(type_distribution.values())
    fig, ax = plt.subplots(figsize=(4.0, 2.6), dpi=130)
    if values:
        ax.pie(values, labels=labels, autopct="%1.0f%%", textprops={"fontsize": 8})
    else:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
    fig.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight", transparent=True)
    plt.close(fig)
    buffer.seek(0)
    return buffer

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
        df = pd.read_csv(dataset.file.path)
        return compute_stats_from_df(df, dataset.id, dataset.uploaded_at)
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

class CompareView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        file_a = request.FILES.get('file_a')
        file_b = request.FILES.get('file_b')

        if not file_a or not file_b:
            return Response(
                {"error": "Both file_a and file_b are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            df_a = pd.read_csv(file_a)
            df_b = pd.read_csv(file_b)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        stats_a, error_a = compute_stats_from_df(df_a)
        if error_a:
            return Response({"error": error_a}, status=status.HTTP_400_BAD_REQUEST)

        stats_b, error_b = compute_stats_from_df(df_b)
        if error_b:
            return Response({"error": error_b}, status=status.HTTP_400_BAD_REQUEST)

        df_a = normalize_dataframe(df_a)
        df_b = normalize_dataframe(df_b)

        def build_map(df):
            equipment_map = {}
            for _, row in df.iterrows():
                name = str(row.get('Equipment Name', '')).strip()
                if not name:
                    continue
                if name not in equipment_map:
                    equipment_map[name] = row
            return equipment_map

        map_a = build_map(df_a)
        map_b = build_map(df_b)
        all_names = sorted(set(map_a.keys()) | set(map_b.keys()))

        def val_or_none(row, key):
            if row is None:
                return None
            value = row.get(key)
            if pd.isna(value):
                return None
            return value

        def delta(a, b):
            if a is None or b is None:
                return None
            try:
                return round(float(b) - float(a), 2)
            except Exception:
                return None

        diff_rows = []
        for name in all_names:
            row_a = map_a.get(name)
            row_b = map_b.get(name)

            flow_a = val_or_none(row_a, 'Flowrate')
            flow_b = val_or_none(row_b, 'Flowrate')
            press_a = val_or_none(row_a, 'Pressure')
            press_b = val_or_none(row_b, 'Pressure')
            temp_a = val_or_none(row_a, 'Temperature')
            temp_b = val_or_none(row_b, 'Temperature')

            row_status = "changed"
            if row_a is None:
                row_status = "only_in_b"
            elif row_b is None:
                row_status = "only_in_a"
            else:
                deltas = [
                    delta(flow_a, flow_b),
                    delta(press_a, press_b),
                    delta(temp_a, temp_b),
                ]
                if all(d == 0 or d is None for d in deltas):
                    row_status = "same"

            diff_rows.append({
                "equipment_name": name,
                "type_a": val_or_none(row_a, 'Type'),
                "type_b": val_or_none(row_b, 'Type'),
                "flowrate_a": flow_a,
                "flowrate_b": flow_b,
                "flowrate_delta": delta(flow_a, flow_b),
                "pressure_a": press_a,
                "pressure_b": press_b,
                "pressure_delta": delta(press_a, press_b),
                "temperature_a": temp_a,
                "temperature_b": temp_b,
                "temperature_delta": delta(temp_a, temp_b),
                "status": row_status,
            })

        diff_summary = {
            "only_in_a": sum(1 for r in diff_rows if r["status"] == "only_in_a"),
            "only_in_b": sum(1 for r in diff_rows if r["status"] == "only_in_b"),
            "in_both": sum(1 for r in diff_rows if r["status"] in ["same", "changed"]),
        }

        return Response(
            {
                "file_a": stats_a,
                "file_b": stats_b,
                "diff": {"summary": diff_summary, "rows": diff_rows},
            },
            status=status.HTTP_200_OK,
        )

class AnalysisReportPdfView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            dataset = EquipmentDataset.objects.get(pk=pk, user=request.user)
        except EquipmentDataset.DoesNotExist:
            return Response({"error": "Dataset not found"}, status=status.HTTP_404_NOT_FOUND)

        stats, error = analyze_dataset(dataset)
        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        buffer = io.BytesIO()
        c = pdf_canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        margin_x = 50
        y = height - 50
        logo_path = None
        possible_logo = [
            os.path.join(os.path.dirname(__file__), "..", "assets", "equipzense.png"),
            os.path.join(os.path.dirname(__file__), "..", "..", "frontend-web", "public", "favicon.png"),
        ]
        for path in possible_logo:
            if os.path.exists(path):
                logo_path = path
                break

        def draw_line(text, size=11, bold=False, spacer=16):
            nonlocal y
            if y < 80:
                c.showPage()
                y = height - 50
            c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
            c.drawString(margin_x, y, text)
            y -= spacer

        if logo_path:
            try:
                c.drawImage(logo_path, margin_x, y - 40, width=36, height=36, mask='auto')
            except Exception:
                pass
        c.setFont("Helvetica-Bold", 22)
        c.drawString(margin_x + 48, y, "Analysis Report")
        y -= 22
        c.setFont("Helvetica", 12)
        c.drawString(margin_x + 48, y, "EquipZense — Analyze. Visualize. Optimize.")
        y -= 22
        draw_line(
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            size=10,
        )
        uploaded_at = stats.get("uploaded_at")
        if uploaded_at:
            draw_line(f"Uploaded at: {uploaded_at}", size=10, spacer=18)

        draw_line("Summary Statistics", size=14, bold=True, spacer=18)
        draw_line(f"Total Equipment Count: {stats.get('total_count', 0)}")
        avgs = stats.get("averages", {})
        draw_line(f"Average Flowrate: {avgs.get('flowrate', 0)}")
        draw_line(f"Average Pressure: {avgs.get('pressure', 0)}")
        draw_line(f"Average Temperature: {avgs.get('temperature', 0)}", spacer=20)

        # Charts
        avg_chart = render_avg_chart(avgs)
        type_chart = render_type_chart(stats.get("type_distribution", {}))
        chart_y = y - 210
        if chart_y < 100:
            c.showPage()
            y = height - 50
            chart_y = y - 210
        c.drawImage(ImageReader(avg_chart), margin_x, chart_y, width=250, height=180, mask='auto')
        c.drawImage(ImageReader(type_chart), margin_x + 270, chart_y, width=250, height=180, mask='auto')
        y = chart_y - 20

        draw_line("Equipment Type Distribution", size=14, bold=True, spacer=18)
        type_dist = stats.get("type_distribution", {})
        if type_dist:
            for key, value in type_dist.items():
                draw_line(f"{key}: {value}", size=10, spacer=14)
        else:
            draw_line("No type data available.", size=10, spacer=14)

        draw_line("Sample Records (Top 10)", size=14, bold=True, spacer=18)
        preview = stats.get("preview", [])
        if not preview:
            draw_line("No records available.", size=10, spacer=14)
        else:
            for row in preview:
                line = (
                    f"{row.get('Equipment Name', '')} | "
                    f"{row.get('Type', '')} | "
                    f"Flowrate: {row.get('Flowrate', '')} | "
                    f"Pressure: {row.get('Pressure', '')} | "
                    f"Temp: {row.get('Temperature', '')}"
                )
                draw_line(line, size=9, spacer=12)

        c.showPage()
        c.save()
        pdf = buffer.getvalue()
        buffer.close()

        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="analysis_report_{pk}.pdf"'
        return response
