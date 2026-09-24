"""
SONAR-X PDF Report Generator
Uses ReportLab to generate professional survey and temporal reports.
"""

from io import BytesIO
from datetime import datetime, timezone
import logging

logger = logging.getLogger('sonarx.reports')

SOFTWARE_VERSION = '0.1.0-prototype'

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm, mm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab not available — PDF generation disabled.")

# SONAR-X brand colors — only defined when ReportLab is available
if REPORTLAB_AVAILABLE:
    NAVY = colors.HexColor('#0A1628')
    OCEAN = colors.HexColor('#0D4F8C')
    CYAN = colors.HexColor('#00B4D8')
    TEAL = colors.HexColor('#0077B6')
    RED = colors.HexColor('#DC2626')
    AMBER = colors.HexColor('#D97706')
    GREEN = colors.HexColor('#059669')
    GRAY = colors.HexColor('#6B7280')
    LIGHT_GRAY = colors.HexColor('#F3F4F6')
else:
    NAVY = OCEAN = CYAN = TEAL = RED = AMBER = GREEN = GRAY = LIGHT_GRAY = None


def _build_styles():
    styles = getSampleStyleSheet()
    custom = {
        'title': ParagraphStyle('SXTitle', parent=styles['Title'],
                                 fontName='Helvetica-Bold', fontSize=22,
                                 textColor=NAVY, spaceAfter=4),
        'subtitle': ParagraphStyle('SXSubtitle', parent=styles['Normal'],
                                    fontName='Helvetica', fontSize=11,
                                    textColor=OCEAN, spaceAfter=12),
        'heading': ParagraphStyle('SXHeading', parent=styles['Heading2'],
                                   fontName='Helvetica-Bold', fontSize=13,
                                   textColor=NAVY, spaceBefore=14, spaceAfter=6),
        'body': ParagraphStyle('SXBody', parent=styles['Normal'],
                                fontName='Helvetica', fontSize=9,
                                textColor=colors.black, spaceAfter=4),
        'caption': ParagraphStyle('SXCaption', parent=styles['Normal'],
                                   fontName='Helvetica-Oblique', fontSize=8,
                                   textColor=GRAY),
        'warning': ParagraphStyle('SXWarning', parent=styles['Normal'],
                                   fontName='Helvetica-Bold', fontSize=10,
                                   textColor=RED, spaceAfter=4),
        'demo': ParagraphStyle('SXDemo', parent=styles['Normal'],
                                fontName='Helvetica-Bold', fontSize=9,
                                textColor=AMBER),
    }
    return custom


class SurveyReportGenerator:
    """Generate a PDF survey report."""

    def __init__(self, survey, detections):
        self.survey = survey
        self.detections = detections

    def generate(self) -> BytesIO:
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("ReportLab is not installed. Cannot generate PDF.")

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            leftMargin=2 * cm, rightMargin=2 * cm,
            topMargin=2 * cm, bottomMargin=2 * cm,
        )

        styles = _build_styles()
        story = []

        # Header
        story.append(Paragraph('SONAR-X', styles['title']))
        story.append(Paragraph('Physics-Aware Explainable Marine Debris Intelligence System', styles['subtitle']))
        story.append(HRFlowable(width='100%', thickness=2, color=OCEAN))
        story.append(Spacer(1, 10))
        story.append(Paragraph('SURVEY INTELLIGENCE REPORT', styles['heading']))
        story.append(Spacer(1, 6))

        # Demo banner
        if self.survey.is_demo or self.survey.data_source == 'DEMO':
            story.append(Paragraph(
                '⚠ DATA SOURCE: DEMO — Synthetic data — not field performance. '
                'All results are demonstration outputs.',
                styles['demo']
            ))
            story.append(Spacer(1, 8))

        # Survey information table
        survey_info = [
            ['Survey ID', self.survey.survey_id],
            ['Survey Name', self.survey.name],
            ['Survey Date', str(self.survey.date)],
            ['Area', self.survey.area or 'Not specified'],
            ['Operator', self.survey.operator or 'Not specified'],
            ['Data Source', self.survey.data_source],
            ['Status', self.survey.status],
            ['Generated', datetime.now(timezone.utc).replace(tzinfo=None).strftime('%Y-%m-%d %H:%M UTC')],
            ['Software', f'SONAR-X {SOFTWARE_VERSION}'],
        ]

        story.append(Paragraph('Survey Information', styles['heading']))
        t = Table(survey_info, colWidths=[5 * cm, 12 * cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, GRAY),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, LIGHT_GRAY]),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

        # Sonar metadata
        story.append(Paragraph('Sonar Metadata', styles['heading']))
        meta = [
            ['Altitude above seabed', f'{self.survey.altitude_m} m' if self.survey.altitude_m else 'Not available'],
            ['Range scale', f'{self.survey.range_scale_mpp} m/px' if self.survey.range_scale_mpp else 'Not available'],
            ['Channel layout', self.survey.channel_layout],
            ['Already gain corrected', 'Yes' if self.survey.already_gain_corrected else 'No'],
            ['Already slant-range corrected', 'Yes' if self.survey.already_slant_range_corrected else 'No'],
        ]
        t2 = Table(meta, colWidths=[7 * cm, 10 * cm])
        t2.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, GRAY),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, LIGHT_GRAY]),
        ]))
        story.append(t2)
        story.append(Spacer(1, 12))

        # Detection statistics
        story.append(Paragraph('Detection Summary', styles['heading']))

        class_counts = {}
        hazard_counts = {'NONE': 0, 'CAUTION': 0, 'HIGH_CAUTION': 0}
        for d in self.detections:
            class_counts[d.classification] = class_counts.get(d.classification, 0) + 1
            hazard_counts[d.hazard_level] = hazard_counts.get(d.hazard_level, 0) + 1

        stats = [
            ['Total detections', str(len(self.detections))],
            ['Marine Debris', str(class_counts.get('MARINE_DEBRIS', 0))],
            ['Natural Formation', str(class_counts.get('NATURAL_FORMATION', 0))],
            ['Sonar Artifact', str(class_counts.get('SONAR_ARTIFACT', 0))],
            ['Unknown Anomaly', str(class_counts.get('UNKNOWN_ANOMALY', 0))],
            ['Hazard — High Caution', str(hazard_counts.get('HIGH_CAUTION', 0))],
            ['Hazard — Caution', str(hazard_counts.get('CAUTION', 0))],
        ]
        t3 = Table(stats, colWidths=[7 * cm, 10 * cm])
        t3.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, GRAY),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, LIGHT_GRAY]),
        ]))
        story.append(t3)
        story.append(Spacer(1, 12))

        # Detection list
        story.append(Paragraph('Detection List', styles['heading']))

        if self.detections:
            det_table_data = [
                ['Detection UID', 'Class', 'Conf.*', 'Evidence*', 'Risk', 'Hazard', 'Lat', 'Lon', 'Status']
            ]
            for d in self.detections:
                det_table_data.append([
                    d.detection_uid or '',
                    d.classification.replace('_', ' '),
                    f'{d.confidence:.0f}',
                    f'{d.evidence_score:.0f}',
                    d.false_positive_risk,
                    d.hazard_level,
                    f'{d.latitude:.4f}' if d.latitude else 'N/A',
                    f'{d.longitude:.4f}' if d.longitude else 'N/A',
                    d.verification_status,
                ])

            col_widths = [3.5*cm, 3.5*cm, 1.2*cm, 1.5*cm, 1.5*cm, 2*cm, 1.8*cm, 1.8*cm, 2.2*cm]
            t4 = Table(det_table_data, colWidths=col_widths, repeatRows=1)
            t4.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), NAVY),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('GRID', (0, 0), (-1, -1), 0.3, GRAY),
                ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ]))
            story.append(t4)
            story.append(Paragraph('* Confidence and Evidence Score are prototype scores, NOT validated probabilities.', styles['caption']))
        else:
            story.append(Paragraph('No detections found for this survey.', styles['body']))

        story.append(Spacer(1, 16))

        # Hazard section
        hazard_dets = [d for d in self.detections if d.hazard_level != 'NONE']
        if hazard_dets:
            story.append(HRFlowable(width='100%', thickness=1, color=RED))
            story.append(Paragraph('⚠ HAZARD ASSESSMENT', styles['warning']))
            story.append(Paragraph(
                'The following detections triggered precautionary hazard flags. '
                'This system does NOT identify specific hazardous objects. '
                '"Potential Hazard — Do Not Disturb" means sonar evidence warrants human review. '
                'Absence of a hazard flag does NOT mean an object is safe.',
                styles['body']
            ))
            story.append(Spacer(1, 6))
            for d in hazard_dets:
                story.append(Paragraph(
                    f'● {d.detection_uid} — {d.hazard_level} — {d.classification}',
                    styles['warning']
                ))
                if d.hazard_indicators:
                    story.append(Paragraph(
                        'Indicators: ' + ', '.join(d.hazard_indicators),
                        styles['body']
                    ))
            story.append(Spacer(1, 12))

        # Limitations
        story.append(HRFlowable(width='100%', thickness=1, color=GRAY))
        story.append(Paragraph('Limitations and Disclaimers', styles['heading']))
        limitations = [
            'This is a prototype system. All detections require human verification before any action.',
            'Confidence and evidence scores are prototype heuristic values, NOT validated probabilities.',
            'Side-scan sonar does not directly provide water temperature or depth.',
            'Conventional side-scan sonar is not a direct bathymetric sensor.',
            'Slant-range correction geometry is approximate where metadata was unavailable.',
            'Geolocation is approximate. GPS coordinates require field calibration.',
            'A missing detection does NOT prove debris was removed or moved.',
            'Absence of a hazard flag does NOT mean an object is safe.',
        ]
        if self.survey.is_demo:
            limitations.insert(0, 'DATA SOURCE: DEMO — Synthetic data — NOT field performance.')

        for lim in limitations:
            story.append(Paragraph(f'• {lim}', styles['body']))

        story.append(Spacer(1, 12))
        story.append(Paragraph(
            'AI-generated observations require verification by qualified human experts.',
            styles['warning']
        ))

        doc.build(story)
        buffer.seek(0)
        return buffer


class TemporalReportGenerator:
    """Generate a PDF temporal intelligence report."""

    def __init__(self, debris_object):
        self.debris = debris_object

    def generate(self) -> BytesIO:
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("ReportLab is not installed. Cannot generate PDF.")

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            leftMargin=2 * cm, rightMargin=2 * cm,
            topMargin=2 * cm, bottomMargin=2 * cm,
        )

        styles = _build_styles()
        story = []

        story.append(Paragraph('SONAR-X', styles['title']))
        story.append(Paragraph('Physics-Aware Explainable Marine Debris Intelligence System', styles['subtitle']))
        story.append(HRFlowable(width='100%', thickness=2, color=OCEAN))
        story.append(Spacer(1, 10))
        story.append(Paragraph('TEMPORAL INTELLIGENCE REPORT', styles['heading']))

        if self.debris.is_demo:
            story.append(Paragraph(
                '⚠ DATA SOURCE: DEMO — Synthetic data — not field performance.',
                styles['demo']
            ))
            story.append(Spacer(1, 8))

        # Debris object info
        story.append(Paragraph('Tracked Object', styles['heading']))
        obj_data = [
            ['Debris UID', self.debris.debris_uid],
            ['First Observed', str(self.debris.first_observed.date()) if self.debris.first_observed else 'N/A'],
            ['Current Status', self.debris.current_status],
            ['Classification', self.debris.classification or 'Unknown'],
            ['Hazard Level', self.debris.hazard_level],
        ]
        t = Table(obj_data, colWidths=[5 * cm, 12 * cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, GRAY),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

        # Observations
        story.append(Paragraph('Survey Timeline', styles['heading']))
        observations = self.debris.observations.all().order_by('timestamp')

        if observations.exists():
            obs_data = [['Survey', 'Date', 'Class', 'Conf.*', 'Lat', 'Lon', 'Hazard']]
            for obs in observations:
                obs_data.append([
                    obs.survey.survey_id,
                    str(obs.timestamp.date()),
                    obs.classification.replace('_', ' ') if obs.classification else 'N/A',
                    f'{obs.confidence:.0f}',
                    f'{obs.latitude:.4f}' if obs.latitude else 'N/A',
                    f'{obs.longitude:.4f}' if obs.longitude else 'N/A',
                    obs.hazard_level,
                ])
            t2 = Table(obs_data, colWidths=[3.5*cm, 2.2*cm, 3.5*cm, 1.5*cm, 2*cm, 2*cm, 2.3*cm], repeatRows=1)
            t2.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), NAVY),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.3, GRAY),
                ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
            ]))
            story.append(t2)
        else:
            story.append(Paragraph('No observations recorded.', styles['body']))

        story.append(Spacer(1, 12))

        # Temporal match info
        matches = self.debris.temporal_matches.all().order_by('-created_at')
        if matches.exists():
            story.append(Paragraph('Temporal Analysis', styles['heading']))
            latest = matches.first()

            match_info = [
                ['Distance to candidate', f'{latest.distance_m:.1f} m' if latest.distance_m else 'N/A'],
                ['Fingerprint Similarity Score', f'{latest.fingerprint_similarity:.2f}' if latest.fingerprint_similarity else 'N/A'],
                ['Status', latest.status],
                ['Notes', latest.notes or ''],
                ['Verified by', latest.verified_by.email if latest.verified_by else 'Not verified'],
                ['Verification comment', latest.verification_comment or '—'],
            ]

            t3 = Table(match_info, colWidths=[5 * cm, 12 * cm])
            t3.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), LIGHT_GRAY),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, GRAY),
                ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, LIGHT_GRAY]),
            ]))
            story.append(t3)
            story.append(Spacer(1, 8))

            story.append(Paragraph(
                'NOTE: "Fingerprint Similarity Score" is a configurable prototype metric. '
                'It is NOT a scientifically validated probability.',
                styles['caption']
            ))

        # Status-specific note
        story.append(Spacer(1, 10))
        if self.debris.current_status == 'POTENTIALLY_RELOCATED':
            story.append(Paragraph(
                '⚠ POTENTIALLY RELOCATED — This label means the object was not detected '
                'at its original location, and a nearby candidate with a similar sonar fingerprint '
                'was found. This is NOT confirmed movement. A missing detection does NOT prove '
                'the object moved. Human expert review is required.',
                styles['warning']
            ))
        elif self.debris.current_status == 'NOT_DETECTED':
            story.append(Paragraph(
                'NOT DETECTED — The object was not found in the follow-up survey at the '
                'original location, and no plausible nearby candidate was identified. '
                'This does NOT prove the object was removed. It may be undetected due to '
                'survey geometry, sonar conditions, or nadir overlap.',
                styles['body']
            ))

        story.append(Spacer(1, 16))

        # Limitations
        story.append(HRFlowable(width='100%', thickness=1, color=GRAY))
        story.append(Paragraph('Limitations', styles['heading']))
        for lim in [
            'A missing detection does NOT prove debris was removed or moved.',
            '"POTENTIALLY RELOCATED" requires human verification. It is not confirmed.',
            'Fingerprint Similarity Score is a prototype metric, NOT a validated probability.',
            'Spatial matching uses Haversine distance which does not account for survey geometry.',
            'AI-generated observations require verification by qualified human experts.',
        ]:
            story.append(Paragraph(f'• {lim}', styles['body']))

        story.append(Spacer(1, 8))
        story.append(Paragraph(
            f'Generated: {datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M UTC")} | '
            f'SONAR-X {SOFTWARE_VERSION} | Team Kurukshetra',
            styles['caption']
        ))

        doc.build(story)
        buffer.seek(0)
        return buffer
