"""
Script to import Q&A data from CSV files into the database
"""

import csv
import os
from app.database import SessionLocal, QAEntry, init_db
from app.services.qa_service import bulk_import_qa

# Initialize database
init_db()
db = SessionLocal()

# CSV file paths
csv_files = [
    "d:/studentassist/drive-download-20260228T050142Z-1-001/Block 1 Arithmetic.csv",
    "d:/studentassist/drive-download-20260228T050142Z-1-001/BLOCK 5 Algebra.csv",
    "d:/studentassist/drive-download-20260228T050142Z-1-001/BLOCK - 7 VARC.csv",
    "d:/studentassist/drive-download-20260228T050142Z-1-001/BLOCK_2_NumberSystem_Arranged.csv",
]

def extract_answer_from_options(options_str: str, correct_answer: str) -> str:
    """
    Parse options string and extract the correct answer.
    Options format: "Option1, Option2, Option3, Option4"
    Correct answer format: "A", "B", "C", or "D" or "(a)", "(b)", etc.
    """
    if not options_str or not correct_answer:
        return correct_answer.strip()
    
    try:
        # Clean up the correct answer
        ans_clean = correct_answer.strip().upper().replace('(', '').replace(')', '')
        if not ans_clean:
            return correct_answer.strip()
        
        # Get the first character which should be A, B, C, or D
        answer_char = ans_clean[0]
        answer_idx = ord(answer_char) - ord('A')
        
        options = [opt.strip() for opt in options_str.split(",")]
        
        if 0 <= answer_idx < len(options):
            return options[answer_idx]
        else:
            return correct_answer.strip()
    except:
        return correct_answer.strip()


def normalize_correct_answer(correct_answer: str) -> str:
    """Normalize correct answer to single letter (A, B, C, D, E)"""
    if not correct_answer:
        return ""
    
    ans_clean = correct_answer.strip().upper().replace('(', '').replace(')', '').strip()
    if ans_clean and len(ans_clean) > 0:
        return ans_clean[0]
    return ""


def import_csv_file(file_path: str):
    """Import Q&A entries from a single CSV file"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return 0
    
    entries = []
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        for row in reader:
            question_text = row.get('Question Text', '').strip()
            if not question_text:
                continue
            
            correct_answer = row.get('Correct Answer', '').strip()
            block = row.get('Block', 'General').strip()
            chapter = row.get('Chapter / Subtopic', 'General').strip()
            difficulty = row.get('Difficulty Level', 'Medium').strip()
            
            # Handle different CSV formats
            # Format 1: "Options / Answer Choices" column (Arithmetic, Algebra, Numbers)
            if 'Options / Answer Choices' in row:
                options = row.get('Options / Answer Choices', '').strip()
                answer = extract_answer_from_options(options, correct_answer)
                question = f"{question_text}\nOptions: {options}" if options else question_text
            
            # Format 2: "Option A", "Option B", etc. columns (VARC)
            elif 'Option A' in row:
                options_list = []
                for opt_key in ['Option A', 'Option B', 'Option C', 'Option D', 'Option E']:
                    opt_val = row.get(opt_key, '').strip()
                    if opt_val:
                        options_list.append(opt_val)
                
                if correct_answer and options_list:
                    # Normalize answer to just letter
                    ans_letter = normalize_correct_answer(correct_answer)
                    if ans_letter:
                        answer_idx = ord(ans_letter) - ord('A')
                        if 0 <= answer_idx < len(options_list):
                            answer = options_list[answer_idx]
                        else:
                            answer = correct_answer.strip()
                    else:
                        answer = correct_answer.strip()
                else:
                    answer = correct_answer.strip()
                
                options_text = " | ".join(options_list) if options_list else ""
                question = f"{question_text}\nOptions: {options_text}" if options_text else question_text
            
            else:
                answer = correct_answer.strip()
                question = question_text
            
            if question and answer:
                entry = {
                    "question": question,
                    "answer": answer,
                    "subject": block,
                    "topic": f"{chapter} ({difficulty})",
                }
                entries.append(entry)
    
    if entries:
        result = bulk_import_qa(entries, db, source="import")
        print(f"✓ {os.path.basename(file_path)}")
        print(f"  Added: {result['added']}, Skipped: {result['skipped']}")
        return result['added']
    
    return 0


def main():
    print("Importing Q&A data from CSV files...")
    print("-" * 50)
    
    total_added = 0
    for file_path in csv_files:
        added = import_csv_file(file_path)
        total_added += added
    
    print("-" * 50)
    print(f"Total entries added: {total_added}")
    
    # Get final stats
    from app.services.qa_service import get_stats
    stats = get_stats(db)
    print(f"\nDatabase stats:")
    print(f"  Total entries: {stats['total']}")
    print(f"  By subject: {stats['by_subject']}")
    
    db.close()


if __name__ == "__main__":
    main()
