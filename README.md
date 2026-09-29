# SONAR-X

## Physics-Aware Explainable Marine Debris Intelligence System

> **DETECT → VERIFY → EXPLAIN → MAP → TRACK**

SONAR-X is an **automated AI-powered Side-Scan Sonar intelligence
system** for detecting, analysing, classifying, explaining and
monitoring underwater marine debris and sonar anomalies.

### Core principle: Upload Once, Automate Everything

The user performs one primary action:

**UPLOAD SIDE-SCAN SONAR DATA**

SONAR-X then automatically performs:

**INGEST → METADATA EXTRACTION → VALIDATION → PREPROCESSING → AI
DETECTION → SONAR FINGERPRINT → EVIDENCE FUSION → CLASSIFICATION →
HAZARD ASSESSMENT → GEOLOCATION → TEMPORAL ANALYSIS → HUMAN VERIFICATION
→ AUTOMATIC PDF REPORT**

------------------------------------------------------------------------

## 1. Problem

Side-Scan Sonar imagery can contain acoustic noise, seabed variation,
geometric distortion, ambiguous targets, natural formations and sonar
artifacts. A detector-only approach can therefore produce false
positives and does not adequately explain why a target was considered
debris.

SONAR-X combines **AI detection, sonar-specific computer vision,
multi-cue evidence fusion, explainability, geospatial intelligence and
temporal monitoring**.

------------------------------------------------------------------------

## 2. Complete Automated Workflow

``` text
USER
  |
  v
UPLOAD SONAR IMAGE / DATA
  |
  v
AUTOMATIC SURVEY CREATION
  |
  v
METADATA EXTRACTION + PROVENANCE
  |
  v
AUTOMATIC VALIDATION
  |
  v
SONAR PREPROCESSING
  |
  v
PYTORCH + YOLO CANDIDATE DETECTION
  |
  v
ROI EXTRACTION
  |
  v
7-CUE SONAR FINGERPRINT
  |
  v
EVIDENCE FUSION
  |
  v
CLASSIFICATION
  |
  +--> MARINE DEBRIS
  +--> NATURAL FORMATION
  +--> SONAR ARTIFACT
  +--> UNKNOWN ANOMALY
  |
  v
EXPLAINABILITY + FALSE-POSITIVE RISK
  |
  v
HAZARD ASSESSMENT
  |
  v
GEOLOCATION / MAP WHEN AVAILABLE
  |
  v
TEMPORAL INTELLIGENCE
  |
  v
HUMAN VERIFICATION FOR UNCERTAIN CASES
  |
  v
AUTOMATIC PDF SURVEY REPORT
```

**No manual survey creation, no manual pipeline-stage execution and no
manual report preparation are required in the automated upload
workflow.**

------------------------------------------------------------------------

## 3. Dashboard

The dashboard provides an operational overview of:

-   Total surveys
-   Total detections
-   Marine debris
-   Natural formations
-   Sonar artifacts
-   Unknown anomalies
-   Hazard flags
-   Pending verification
-   Processing-engine status
-   Temporal intelligence
-   Recent survey activity

------------------------------------------------------------------------

## 4. Backend Architecture

The backend is built with **Python, Django and Django REST Framework**.

When the upload reaches the ingestion API, the backend automatically:

1.  Receives the sonar file.
2.  Creates the survey record.
3.  Extracts available metadata.
4.  Validates the input.
5.  Starts the processing pipeline.
6.  Runs preprocessing.
7.  Runs AI detection.
8.  Generates sonar fingerprints.
9.  Performs evidence fusion.
10. Classifies detections.
11. Performs precautionary hazard assessment.
12. Processes available geospatial metadata.
13. Performs temporal comparison when historical surveys exist.
14. Stores the results.
15. Generates the final PDF report.

Conceptually:

``` text
POST /api/surveys/ingest/
        |
        v
Ingestion Service
        |
        +--> Metadata Extractor
        +--> Validation
        +--> Preprocessing
        +--> AI Inference
        +--> Fingerprint Engine
        +--> Evidence Fusion
        +--> Classification
        +--> Hazard Engine
        +--> Geospatial Processing
        +--> Temporal Engine
        +--> Report Generator
```

------------------------------------------------------------------------

## 5. AI and Computer Vision

### YOLO + PyTorch

SONAR-X uses a **YOLO-based detection pipeline implemented with
PyTorch** for candidate detection.

YOLO identifies potential target regions. It is intentionally **not the
complete intelligence layer**.

The detected regions are passed to the sonar-specific analysis pipeline
for deeper verification.

### OpenCV

OpenCV handles computer-vision operations including:

-   Image loading
-   Resizing
-   Normalization
-   Denoising
-   Contrast enhancement
-   ROI processing
-   Image transformations

### NumPy

NumPy supports numerical processing and feature computation throughout
the sonar pipeline.

------------------------------------------------------------------------

## 6. Seven-Cue Sonar Fingerprint

Every candidate can be analysed using seven sonar-specific evidence
cues:

1.  **Backscatter / Intensity**
2.  **Texture**
3.  **Geometry**
4.  **Acoustic Shadow**
5.  **Object-Shadow Relationship**
6.  **Seabed Context**
7.  **Signal Quality**

These cues provide information beyond a simple bounding box.

------------------------------------------------------------------------

## 7. Evidence Fusion and Explainability

The Evidence Fusion Engine combines the available sonar cues to produce
an explainable result.

The classification categories are:

-   **Marine Debris**
-   **Natural Formation**
-   **Sonar Artifact**
-   **Unknown Anomaly**

The result can include:

-   Classification
-   Confidence
-   Evidence score
-   Supporting evidence
-   Opposing evidence
-   False-positive risk
-   Processing information
-   Geospatial information when available

The objective is to move from:

> **"The model detected something."**

to:

> **"The system detected a candidate, analysed sonar-specific evidence
> and explained the basis and uncertainty of the result."**

------------------------------------------------------------------------

## 8. Hazard Intelligence

SONAR-X provides precautionary hazard assessment:

-   `NONE`
-   `CAUTION`
-   `HIGH CAUTION`

The hazard layer is decision support, not definitive identification of a
specific hazardous object.

High-caution observations can be routed to human verification.

------------------------------------------------------------------------

## 9. Geospatial Intelligence

The system uses:

-   **PostgreSQL** for structured application data
-   **PostGIS** for geospatial data
-   **GeoJSON** for geographic interchange
-   **Leaflet** for map visualization
-   **CSV / KML / GeoJSON** exports

Coordinates are used only when legitimate acquisition/navigation
metadata is available. Missing metadata is not fabricated.

------------------------------------------------------------------------

## 10. Temporal Intelligence

For repeat surveys, SONAR-X compares historical and new detections using
factors such as:

-   Spatial proximity
-   Classification
-   Geometry
-   Sonar fingerprint similarity

Possible temporal states include:

-   **STILL PRESENT**
-   **NOT DETECTED**
-   **POTENTIALLY RELOCATED**
-   **POSSIBLE MATCH**
-   **NEW DETECTION**
-   **REQUIRES VERIFICATION**

A potentially relocated observation remains a hypothesis requiring
verification; non-detection does not automatically prove movement or
removal.

------------------------------------------------------------------------

## 11. Human-in-the-Loop

The goal is not to eliminate expert responsibility.

The goal is to **automate repetitive analysis and reserve human
attention for uncertain or operationally important cases**.

Human verification can be used for:

-   Unknown anomalies
-   High-risk observations
-   Low-confidence detections
-   Potentially relocated objects
-   Hard negatives
-   Operational confirmation

------------------------------------------------------------------------

## 12. Automatic PDF Reporting

After processing, SONAR-X automatically generates a structured survey
intelligence report containing, where available:

### Survey Information

-   Survey ID
-   Survey name
-   Acquisition information
-   Metadata

### Processing Information

-   Validation
-   Preprocessing
-   Detection
-   Fingerprint generation
-   Evidence fusion
-   Classification

### Detection Information

-   Detection ID
-   Classification
-   Confidence
-   Evidence
-   Risk information
-   Fingerprint information
-   Hazard information
-   Geospatial information

The user does not have to manually compile this report.

------------------------------------------------------------------------

## 13. Technology Stack

  Layer                  Technology
  ---------------------- --------------------------
  Frontend               React + TypeScript
  Build                  Vite
  Styling                Tailwind CSS
  Maps                   Leaflet
  Backend                Python + Django
  API                    Django REST Framework
  AI Framework           PyTorch
  Detection              YOLO-based pipeline
  Computer Vision        OpenCV
  Numerical Processing   NumPy
  Database               PostgreSQL
  Geospatial Database    PostGIS
  Geographic Format      GeoJSON
  Exports                CSV / KML / GeoJSON
  Reporting              Automated PDF generation

------------------------------------------------------------------------

## 14. Automation Advantage

SONAR-X follows an **Upload Once → Automate Everything** architecture.

The user's routine responsibility is reduced to:

### **1. Upload the Side-Scan Sonar data.**

The system automatically performs:

**Ingest → Extract → Validate → Preprocess → Detect → Fingerprint → Fuse
→ Classify → Assess → Map → Track → Verify → Report**

The project targets **up to approximately 90% reduction in routine
manual workflow effort**, while retaining human verification for
uncertain and operationally important observations.

------------------------------------------------------------------------

## 15. Key Differentiator

SONAR-X is not simply a YOLO-based detector.

It combines:

``` text
AI Detection
      +
Sonar-Specific Processing
      +
7-Cue Sonar Fingerprint
      +
Evidence Fusion
      +
Explainable Classification
      +
Hazard Awareness
      +
Geospatial Intelligence
      +
Temporal Monitoring
      +
Human Verification
      +
Automatic Reporting
```

This creates a complete chain from **raw sonar input to explainable
marine intelligence**.

------------------------------------------------------------------------

## 16. Scientific Safeguards

SONAR-X follows these safeguards:

-   Missing metadata is not fabricated.
-   GPS is only used when legitimate location information is available.
-   Hazard flags are precautionary.
-   Temporal disappearance does not automatically prove movement or
    removal.
-   Potential relocation requires verification.
-   Prototype/demo data is not represented as field validation.
-   Formal evaluation metrics are reported only when a documented
    evaluation dataset is available.

------------------------------------------------------------------------

## 17. Project Vision

SONAR-X aims to transform Side-Scan Sonar analysis from a largely manual
inspection workflow into an **automated, explainable and traceable
marine intelligence pipeline**.

``` text
RAW SONAR DATA
      ↓
AUTOMATED SCREENING
      ↓
EXPLAINABLE EVIDENCE
      ↓
VERIFICATION
      ↓
GEOSPATIAL + TEMPORAL INTELLIGENCE
      ↓
AUTOMATIC REPORT
```

### SONAR-X

**Detect. Verify. Explain. Map. Track.**

**Team Kurukshetra**\
**Smart India Hackathon 2026**

**Problem Statement:** AI-Powered Automated Underwater Marine Debris and
Anomaly Detection System using Side-Scan Sonar
