# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
Weekly Pattern Mining Script
Run this to discover new patterns and update the normalizer.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from system.input_processing.pattern_miner import PatternMiner
from system.input_processing.input_normalizer import InputNormalizer


def main():
    """Run weekly pattern mining."""
    
    print("="*80)
    print("PATTERN MINING - Weekly Discovery")
    print("="*80 + "\n")
    
    # Initialize
    miner = PatternMiner(min_frequency=5, min_confidence=0.6)  # Lower thresholds for testing
    normalizer = InputNormalizer()
    
    # Load feedback logs
    log_file = "satya_data/normalization_logs/feedback_db.jsonl"
    print(f"Loading logs from: {log_file}\n")
    
    logs = miner.load_feedback_logs(log_file)
    
    if not logs:
        print("❌ No logs found. Run the system first to generate logs.\n")
        return
    
    # Mine patterns
    print("🔍 Mining patterns...\n")
    suggestions = miner.mine_new_patterns(logs)
    
    if not suggestions:
        print("✅ No new patterns found. System is performing well!\n")
        return
    
    # Generate report
    report_file = "satya_data/normalization_logs/pattern_mining_report.md"
    miner.generate_report(suggestions, report_file)
    print(f"📊 Report generated: {report_file}\n")
    
    # Interactive review
    print("="*80)
    print("PATTERN REVIEW (Human-in-the-Loop)")
    print("="*80 + "\n")
    
    approved_count = 0
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"[{i}/{len(suggestions)}] Found pattern:")
        print(f"  Phrase: \"{suggestion['phrase']}\"")
        print(f"  Frequency: {suggestion['frequency']} times")
        print(f"  Confidence: {suggestion['confidence']:.2f}")
        print(f"  Examples:")
        for ex in suggestion['examples']:
            print(f"    - \"{ex}\"")
        print()
        
        choice = input("  Add to noise phrases? (y/n/q to quit): ").strip().lower()
        
        if choice == 'q':
            break
        elif choice == 'y':
            # Add to normalizer
            normalizer.add_noise_phrase(suggestion['phrase'])
            approved_count += 1
            print(f"  ✅ Added!\n")
        else:
            print(f"  ⏭️  Skipped\n")
    
    print("="*80)
    print(f"✅ Approved {approved_count} new patterns")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
