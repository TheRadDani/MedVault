"""
Synthetic Medical Dataset Generator for MedVault RAG pipeline.

Generates realistic clinical notes using Faker for testing and development.
Supports optional encryption at rest for HIPAA compliance.
"""

import os
import random
from pathlib import Path
from faker import Faker
from datetime import datetime, timedelta
from loguru import logger
from src.encryption import get_encryption_manager

fake = Faker()

CONDITIONS = [
    "Type 2 Diabetes",
    "Hypertension",
    "Asthma",
    "Coronary Artery Disease",
    "Osteoarthritis"
]

MEDICATIONS = [
    "Metformin",
    "Lisinopril",
    "Albuterol",
    "Atorvastatin",
    "Ibuprofen"
]

SIDE_EFFECTS = [
    "nausea",
    "dizziness",
    "headache",
    "fatigue",
    "dry mouth"
]


def generate_clinical_note(patient_id: str) -> str:
    """
    Generate a realistic unstructured clinical note.
    
    Args:
        patient_id: Unique patient identifier
    
    Returns:
        Formatted clinical note as string
    """
    condition = random.choice(CONDITIONS)  # Fixed: was 'choicre'
    medication = random.choice(MEDICATIONS)
    age = random.randint(30, 90)
    
    note = f"""
PATIENT ID: {patient_id}
DATE: {fake.date_this_decade()}
AGE: {age}

SUBJECTIVE: Patient presents with complaints of {random.choice(SIDE_EFFECTS)} regarding their {condition}.
Patient states they have been adhering to {medication} therapy but feels "foggy".

OBJECTIVE: BP {random.randint(110, 160)}/{random.randint(70, 100)}. HR {random.randint(60, 100)}.
Labs show HbA1c of {round(random.uniform(5.5, 9.0), 1)}%.

ASSESSMENT: {condition} currently uncontrolled. Suspected side effect from {medication}.

PLAN: 
1. Adjust {medication} dosage.
2. Order metabolic panel.
3. Patient education regarding diet and exercise provided.
4. Follow up in 4 weeks.

Signed, Dr. {fake.last_name()}
"""
    return note.strip()


def generate_dataset(
    count: int = 50,
    output_dir: str = "data/synthetic",
    encrypt: bool = True,
    encryption_key: str = None,
    encryption_password: str = None,
    encrypted_output_dir: str = "data/encrypted"
) -> bool:
    """
    Generate synthetic clinical notes dataset with optional encryption.
    
    Args:
        count: Number of documents to generate
        output_dir: Output directory path for plaintext (temporary)
        encrypt: Whether to encrypt files
        encryption_key: Fernet encryption key (base64-encoded)
        encryption_password: Password for PBKDF2 key derivation
        encrypted_output_dir: Directory to store encrypted files
    
    Returns:
        bool: Success status
    
    Security Notes:
        - If encrypt=True, plaintext files are written temporarily to output_dir
        - Encrypted versions are written to encrypted_output_dir
        - In production, delete plaintext files after encryption
        - Encryption key should be stored in environment variable or secure vault
    """
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating {count} synthetic clinical notes...")
        
        # Generate plaintext files
        for i in range(count):
            pid = f"PID{str(i+1).zfill(4)}"
            note = generate_clinical_note(pid)
            filename = os.path.join(output_dir, f"{pid}_visit_{i}.txt")
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(note)
        
        logger.info(f"✓ Generated {count} clinical notes in '{output_dir}' directory")
        
        # Encrypt files if requested
        if encrypt:
            try:
                # Get encryption manager
                em = get_encryption_manager(
                    encryption_key=encryption_key,
                    password=encryption_password
                )
                
                if not em.encryption_enabled:
                    logger.warning("Encryption not enabled (no key/password). Skipping encryption.")
                    return True
                
                # Create encrypted output directory
                Path(encrypted_output_dir).mkdir(parents=True, exist_ok=True)
                
                # Encrypt all files
                encrypted_count = em.encrypt_directory(
                    input_dir=output_dir,
                    output_dir=encrypted_output_dir
                )
                
                logger.info(f"✓ Encrypted {encrypted_count} files to '{encrypted_output_dir}'")
                logger.warning(
                    "⚠️  SECURITY: Plaintext files still exist in '{}'. "
                    "Delete them manually after verifying encrypted versions: "
                    "rm -rf {}".format(output_dir, output_dir)
                )
                
            except Exception as e:
                logger.error(f"Encryption failed: {e}", exc_info=True)
                logger.warning("Continuing with plaintext files only")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate dataset: {e}", exc_info=True)
        return False



if __name__ == "__main__":
    # Configure logging for standalone execution
    from loguru import logger
    logger.enable("__main__")
    
    # Generate default dataset
    success = generate_dataset()
    if not success:
        exit(1)
