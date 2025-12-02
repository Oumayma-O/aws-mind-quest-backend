from sqlalchemy.orm import Session
from app.database.models import Certification, CertificationDocument
from app.utils.s3 import parse_s3_path, s3_object_exists
import logging
logger = logging.getLogger(__name__)

PREDEFINED_CERTIFICATIONS = [
    {
        "name": "AWS Cloud Practitioner",
        "description": "Foundational AWS certification for cloud concepts and core services.",
        "documents": [
            {
                "s3_uri": "s3://aws-mind-quest-bucket/certifications/AWS-Certified-Cloud-Practitioner_Exam-Guide.pdf"
            }
        ]
    },
    {
        "name": "AWS Solutions Architect Associate",
        "description": "Designing and deploying scalable systems on AWS.",
        "documents": [
            {
                "s3_uri": "s3://aws-mind-quest-bucket/certifications/AWS-Certified-Solutions-Architect-Associate_Exam-Guide.pdf"
            }
        ]
    },
    {
        "name": "AI Practitioner",
        "description": "Introductory certification for applying AI solutions.",
        "documents": [
            {
                "s3_uri": "s3://aws-mind-quest-bucket/certifications/AWS-Certified-AI-Practitioner_Exam-Guide.pdf"
            }
        ]
    },
    {
        "name": "Machine Learning Engineer Associate",
        "description": "Building and training ML models on AWS.",
        "documents": [
            {
                "s3_uri": "s3://aws-mind-quest-bucket/certifications/AWS-Certified-Machine-Learning-Engineer-Associate_Exam-Guide.pdf"
            }
        ]
    },
    {
        "name": "AWS Certified Machine Learning Specialty",
        "description": "Validates advanced expertise in building, training, tuning, and deploying machine learning models on AWS, covering data engineering, exploratory data analysis, modeling, and ML implementation and operations.",
        "documents": [
            {
                "s3_uri": "s3://aws-mind-quest-bucket/certifications/AWS-Certified-Machine-Learning-Specialty_Exam-Guide.pdf"
            }
        ]
    },
    {
        "name": "AWS Certified DevOps Engineer Professional",
        "description": "Advanced ops, automation and CI/CD on AWS."
    },
]


def seed_certifications(db: Session):
    """Insert predefined certifications if they don't already exist. Returns list of document IDs to process."""
    documents_to_process = []
    
    for cert in PREDEFINED_CERTIFICATIONS:
        existing = db.query(Certification).filter(Certification.name == cert["name"]).first()
        if existing:
            logger.info(f"Certification already exists: {cert['name']}")
            # Ensure documents exist in DB for existing certification
            docs = cert.get("documents", [])
            for d in docs:
                # determine url/key
                s3_path = d.get("s3_uri") or d.get("https_url") or d.get("url")
                if not s3_path:
                    continue
                try:
                    bucket, key, url = parse_s3_path(s3_path)
                except ValueError:
                    logger.warning(f"Skipping invalid s3 path in seed: {s3_path}")
                    continue

                # avoid duplicates
                exists_doc = db.query(CertificationDocument).filter(
                    CertificationDocument.certification_id == existing.id,
                    CertificationDocument.s3_key == key
                ).first()
                if exists_doc:
                    # Check if existing document needs processing
                    if exists_doc.processing_status != "completed":
                        documents_to_process.append((str(exists_doc.id), str(existing.id)))
                    continue

                # only create a record if object exists in S3
                if s3_object_exists(bucket, key):
                    doc = CertificationDocument(
                        certification_id=existing.id,
                        filename=key.split('/')[-1],
                        s3_key=key,
                        uri=s3_path  # Store S3 URI
                    )
                    db.add(doc)
                    db.flush()  # Get doc.id
                    documents_to_process.append((str(doc.id), str(existing.id)))
                else:
                    logger.warning(f"S3 object not found for seed: s3://{bucket}/{key}")
            continue
        c = Certification(name=cert["name"], description=cert.get("description", ""))
        db.add(c)
        db.flush()

        # attach documents if provided
        docs = cert.get("documents", [])
        for d in docs:
            s3_uri = d.get("s3_uri") or d.get("https_url") or d.get("url")
            if not s3_uri:
                continue
            
            # Extract bucket and key from S3 URI
            try:
                bucket, key, _ = parse_s3_path(s3_uri)
            except ValueError:
                logger.warning(f"Skipping invalid s3 path in seed: {s3_uri}")
                continue

            if s3_object_exists(bucket, key):
                doc = CertificationDocument(
                    certification_id=c.id,
                    filename=key.split('/')[-1],
                    s3_key=key,
                    uri=s3_uri  # Store S3 URI directly
                )
                db.add(doc)
                db.flush()  # Get doc.id
                documents_to_process.append((str(doc.id), str(c.id)))
            else:
                logger.warning(f"S3 object not found for seed: s3://{bucket}/{key}")
    try:
        db.commit()
        logger.info(f"Seeded predefined certifications. {len(documents_to_process)} documents to process.")
        return documents_to_process
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed certifications: {e}")
        return []
