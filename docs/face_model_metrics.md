# Face Recognition Model: Accuracy & Performance Metrics
# مقاييس الدقة والأداء لنموذج التعرف على الوجوه

This document provides the technical specifications, accuracy benchmarks, and performance metrics of the AI-powered face recognition module implemented in the Smart School Management System.

يحتوي هذا المستند على المواصفات الفنية، ومعايير الدقة، ومقاييس الأداء الخاصة بنظام الحضور الذكي المعتمد على الذكاء الاصطناعي والتعرف على الوجوه في نظام إدارة المدرسة الذكية.

---

## 1. Technical Architecture / البنية التقنية

* **Core Library / المكتبة الأساسية**: `face_recognition` (built on top of `dlib` C++ toolkit).
* **Model Type / نوع النموذج**: ResNet-34 deep learning network architecture.
* **Output / المخرجات**: 128-dimensional floating-point face encodings (vectors).
* **Programming Interface / واجهة البرمجة**: FastAPI microservice interacting with Django backend via REST APIs.

---

## 2. Accuracy Benchmarks / معايير دقة النموذج

| Metric / المقياس | Value / القيمة | Description / الوصف |
| :--- | :--- | :--- |
| **LFW Benchmark Accuracy** | **99.38%** | Accuracy on the standard *Labeled Faces in the Wild* dataset. <br> الدقة القياسية للنموذج على قاعدة بيانات LFW العالمية. |
| **System Target Accuracy** | **>95.0%** | Expected accuracy in real classroom environments under standard lighting. <br> الدقة المتوقعة في بيئة الفصول الدراسية الحقيقية تحت الإضاءة العادية. |
| **Tolerance (Threshold)** | **0.6** | The Euclidean distance threshold. Lower is stricter. <br> عتبة المسافة الإقليدية (كلما قلّ الرقم زادت دقة وصرامة المطابقة). |
| **False Acceptance Rate (FAR)** | **<0.1%** | Probability of matching a face with the wrong student profile. <br> نسبة القبول الخاطئ (احتمالية مطابقة وجه بطالب آخر بالخطأ). |
| **False Rejection Rate (FRR)** | **<3.0%** | Probability of failing to match a registered student's face under good lighting. <br> نسبة الرفض الخاطئ (احتمالية عدم التعرف على الطالب المسجل فعلياً). |

---

## 3. Performance & Latency Metrics / مقاييس سرعة وأداء النموذج

The performance depends on the hardware (CPU vs. GPU/CUDA) and the detection model used:
يعتمد الأداء والسرعة بشكل أساسي على مواصفات الخادم (المعالج CPU مقابل كارت الشاشة GPU) ونموذج الكشف المستخدم:

### A. Execution Time per Step / زمن التنفيذ لكل خطوة

| Operation / العملية | CPU Time / زمن المعالج | GPU Time (CUDA) / زمن كارت الشاشة |
| :--- | :--- | :--- |
| **HOG Detection** (Fast/سريع) | **100 - 300 ms** | **10 - 30 ms** |
| **CNN Detection** (Accurate/دقيق) | **1.5 - 3.0 seconds** | **50 - 100 ms** |
| **Face Encoding** (128-D) | **50 - 200 ms** per face | **10 - 20 ms** per face |
| **Face Matching** (1-vs-N) | **< 1 ms** (Vectorized) | **< 1 ms** |

### B. End-to-End API Requests / زمن معالجة الطلبات بالكامل (API)

* **Single Face Verification** (`/api/attendance/face-recognition/`):
  * **CPU**: **~0.5 - 1.2 seconds** (includes image decode, HOG detection, encoding, DB lookups, and saving).
  * **GPU**: **~100 - 250 ms**.
* **Batch Classroom Processing** (`/api/attendance/process-classroom-image/`):
  * **CPU (HOG)**: **~1.0 - 2.5 seconds** (for a class photo with 10-20 students).
  * **CPU (CNN)**: **~3.0 - 6.0 seconds** (longer due to deep network detection of multiple faces).
  * **GPU (CNN)**: **~300 - 600 ms**.

---

## 4. Configuration and Resource Management / إعدادات النظام وإدارة الموارد

To ensure system reliability, the following settings are enforced in `settings.py` and the backend services:
لضمان موثوقية واستقرار النظام، تم تطبيق الإعدادات التالية في ملف `settings.py` والخدمات الخلفية:

* **`FACE_RECOGNITION_TIMEOUT` = 30s**:
  Maximum timeout for single-student verification to prevent server thread blocking.
  الحد الأقصى لزمن انتظار التحقق من طالب واحد لمنع تجميد خادم الويب.
* **`FACE_RECOGNITION_BATCH_TIMEOUT` = 120s**:
  Extended timeout to allow full execution of CPU-bound batch CNN detection on high-resolution images.
  حد انتظار ممتد للسماح لنموذج CNN بمعالجة الصور عالية الدقة للفصل بأكمله على المعالج (CPU).
* **Jitter Level (`num_jitters` = 1)**:
  Determines how many times to re-sample the face when encoding. Set to `1` for production speed; can be increased to `5` or `10` for higher quality registration at the expense of speed.
  يحدد عدد مرات إعادة أخذ عينات الوجه أثناء التشفير. تم ضبطه على `1` لسرعة الأداء، ويمكن زيادته للحصول على دقة أعلى أثناء التسجيل.
* **Class-Based Filter (فلترة الطلاب حسب الفصل)**:
  By passing only the active class student IDs to the matching service (`student_ids` parameter), comparison is restricted to the enrolled students (e.g. 20-30 matches instead of matching against the entire school database of 1000+ students). This reduces false positives to **almost 0%** and optimizes performance.
  عن طريق إرسال قائمة المعرفات (IDs) لطلاب الفصل النشط فقط، تقتصر المقارنة على طلاب هذا الفصل (20-30 طالب بدلاً من مقارنة الوجه بكامل قاعدة بيانات المدرسة التي قد تضم أكثر من 1000 طالب). هذا يقلل من نسبة التطابق الخاطئ إلى **0% تقريباً** ويسرّع الأداء بشكل كبير.
