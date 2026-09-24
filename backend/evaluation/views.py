"""SONAR-X Evaluation Views"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import EvaluationRun, EvaluationDataset


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def evaluation_runs(request):
    runs = EvaluationRun.objects.all().order_by('-timestamp')
    if not runs.exists():
        return Response({
            'status': 'NOT_EVALUATED',
            'message': (
                'No evaluation runs exist for this system. '
                'Evaluation metrics will only be shown when a genuine '
                'held-out evaluation is performed.'
            ),
            'runs': [],
        })

    data = []
    for run in runs:
        data.append({
            'id': str(run.id),
            'model_version': run.model_version,
            'configuration_version': run.configuration_version,
            'inference_mode': run.inference_mode,
            'timestamp': run.timestamp.isoformat(),
            'metrics': run.metrics,
            'per_class_metrics': run.per_class_metrics,
            'confusion_matrix': run.confusion_matrix,
            'dataset': {
                'name': run.dataset.name,
                'synthetic': run.dataset.synthetic,
                'image_count': run.dataset.image_count,
                'object_count': run.dataset.object_count,
            },
            'notes': run.notes,
            'small_sample_warning': run.small_sample_warning,
            'synthetic_data_warning': run.dataset.synthetic,
        })

    return Response({'status': 'HAS_RUNS', 'runs': data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def latest_evaluation_run(request):
    run = EvaluationRun.objects.order_by('-timestamp').first()
    if not run:
        return Response({
            'status': 'NOT_EVALUATED',
            'message': 'No evaluation runs exist.',
        })

    return Response({
        'status': 'HAS_RUN',
        'run': {
            'id': str(run.id),
            'model_version': run.model_version,
            'inference_mode': run.inference_mode,
            'timestamp': run.timestamp.isoformat(),
            'metrics': run.metrics,
            'per_class_metrics': run.per_class_metrics,
            'dataset_synthetic': run.dataset.synthetic,
            'small_sample_warning': run.small_sample_warning,
        }
    })
