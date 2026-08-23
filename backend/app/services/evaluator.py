import re
from typing import Optional

def levenshtein_distance(seq1, seq2):
    m, n = len(seq1), len(seq2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i - 1] == seq2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[m][n]

def compute_accuracy_metrics(extracted_text: str, ground_truth: Optional[str] = None) -> dict:
    if not ground_truth or not ground_truth.strip():
        return {
            "available": False,
            "ground_truth": None,
            "cer": None,
            "wer": None,
            "message": "Not available — ground truth not provided"
        }
    
    gt_clean = ground_truth.strip()
    hyp_clean = extracted_text.strip()
    
    # CER Calculation (character level)
    gt_chars = list(gt_clean)
    hyp_chars = list(hyp_clean)
    if not gt_chars:
        cer = 0.0
    else:
        dist_c = levenshtein_distance(gt_chars, hyp_chars)
        cer = round((dist_c / len(gt_chars)) * 100, 2)
        
    # WER Calculation (word level)
    gt_words = re.findall(r'\S+', gt_clean)
    hyp_words = re.findall(r'\S+', hyp_clean)
    if not gt_words:
        wer = 0.0
    else:
        dist_w = levenshtein_distance(gt_words, hyp_words)
        wer = round((dist_w / len(gt_words)) * 100, 2)
        
    return {
        "available": True,
        "ground_truth": gt_clean,
        "cer": cer,
        "wer": wer,
        "message": f"Evaluated: CER {cer}%, WER {wer}%"
    }
