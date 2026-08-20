import os
from PIL import Image, ImageDraw, ImageFont

def generate_samples():
    base_dir = "test-data"
    
    samples = {
        "01-clean": ("sample_clean.png", "INVOICE #INV-9081\nDate: 2026-08-20\nAmount Due: $1,250.00\nPayment Terms: Net 30", "Clean Printed Document"),
        "02-scanned": ("sample_scanned.png", "TAX DEDUCTION CERTIFICATE\nAssessment Year: 2025-2026\nTotal Tax Retained: INR 45,000\nStatus: Verified", "Scanned Tax Certificate"),
        "03-multicolumn": ("sample_multicolumn.png", "COLUMN 1: Sales Analysis\nNorth Region: $40,000\nSouth Region: $55,000\n\nCOLUMN 2: Operational Highlights\nExpansion complete.\nCustomer retention: 94%", "Multi-Column Report"),
        "04-tables": ("sample_table.png", "ITEM | QTY | PRICE | TOTAL\nLaptop Stand | 2 | $45.00 | $90.00\nUSB-C Cable | 5 | $12.00 | $60.00\nWireless Mouse | 1 | $35.00 | $35.00", "Itemized Table"),
        "05-forms": ("sample_form.png", "PATIENT REGISTRATION FORM\nName: Aaryan Shukla\nDOB: 15/04/1998\nPhone: +91 9876543210\nBlood Group: O+", "Form Document"),
        "06-invoices": ("invoice_01.png", "TAX INVOICE\nInvoice No: INV-1024\nCustomer: Acme Corp\nSubtotal: INR 42,372.88\nGST (18%): INR 7,627.12\nTotal: INR 50,000.00", "Standard Tax Invoice"),
        "07-receipts": ("receipt_02.png", "STAR COFFEE HOUSE\nOrder #4201\n1x Cappuccino - $4.50\n1x Croissant - $3.75\nTotal Paid: $8.25\nThank you for visiting!", "Store Receipt"),
        "08-camera": ("camera_snap.jpg", "WARNING: AUTHORIZED PERSONNEL ONLY\nKeep door closed at all times.\nEmergency Contact: Ext 4091", "Camera Snapshot"),
        "09-blur-noise": ("noisy_doc.png", "CONFIDENTIAL REPORT\nProject Alpha Status: Green\nBudget Allocated: $500,000", "Noisy Document"),
        "10-rotated": ("rotated_90.png", "ORIENTED TEXT BLOCK\nRotating 90 degrees test.\nPaddleOCR text orientation check.", "Rotated Document"),
        "11-multilingual": ("multilingual.png", "ENGLISH: Welcome to the System\nHINDI: Softare Evaluation\nNUMBERS: 1234567890", "Multilingual Document"),
        "12-handwritten": ("handwritten_note.png", "Note: Review PaddleOCR accuracy\nCheck CER and WER scores\nMeeting at 4:00 PM today!", "Handwritten Note Sample"),
        "13-extreme": ("extreme_dense.png", "DENSE DATA MATRIX: A1-902-881-X // B4-112-990-Y // C7-441-002-Z\nSERIAL: 9912048102948192-OK", "Dense Data Code")
    }

    for cat_folder, (filename, content, title) in samples.items():
        folder_path = os.path.join(base_dir, cat_folder)
        os.makedirs(folder_path, exist_ok=True)
        
        img_path = os.path.join(folder_path, filename)
        gt_path = os.path.join(folder_path, filename.rsplit('.', 1)[0] + ".txt")
        
        # Create ground truth text file
        with open(gt_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # Create synthetic image for test category
        lines = content.split('\n')
        h = max(300, len(lines) * 40 + 80)
        w = 650
        img = Image.new("RGB", (w, h), color=(250, 250, 252))
        draw = ImageDraw.Draw(img)
        
        # Draw header banner
        draw.rectangle([(0, 0), (w, 50)], fill=(30, 41, 59))
        draw.text((20, 15), f"Category Test: {cat_folder.upper()} - {title}", fill=(255, 255, 255))
        
        y = 70
        for line in lines:
            if line.strip():
                draw.text((30, y), line, fill=(15, 23, 42))
                y += 38
                
        img.save(img_path)
        print(f"Generated sample in {cat_folder}: {filename}")

if __name__ == "__main__":
    generate_samples()
