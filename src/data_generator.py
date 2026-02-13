"""
Synthetic Medical Dataset Generator for MedVault RAG pipeline.

Generates realistic clinical notes using Faker for testing and development.
"""

import os
import random
from faker import Faker
from datetime import datetime, timedelta
from loguru import logger

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


def generate_dataset(count: int = 50, output_dir: str = "data/synthetic") -> bool:
    """
    Generate synthetic clinical notes dataset.
    
    Args:
        count: Number of documents to generate
        output_dir: Output directory path
    
    Returns:
        bool: Success status
    """
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"Generating {count} synthetic clinical notes...")
        
        for i in range(count):
            pid = f"PID{str(i+1).zfill(4)}"
            note = generate_clinical_note(pid)
            filename = os.path.join(output_dir, f"{pid}_visit_{i}.txt")
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(note)
        
        logger.info(f"✓ Generated {count} clinical notes in '{output_dir}' directory")
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
