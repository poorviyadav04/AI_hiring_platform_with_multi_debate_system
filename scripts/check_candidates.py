"""
Check for manually-added (non-generated) candidates in the dataset.

This script identifies candidates that don't follow the auto-generated pattern.
"""

import json
from pathlib import Path
import re

def check_candidates():
    """Check for non-generated candidate data."""
    
    data_dir = Path(__file__).parent.parent / "data"
    candidates_file = data_dir / "candidates.json"
    
    with open(candidates_file, 'r') as f:
        candidates = json.load(f)
    
    print("=" * 70)
    print("CANDIDATE DATA AUDIT")
    print("=" * 70)
    print(f"\nTotal candidates in file: {len(candidates)}")
    
    # Check for expected pattern: CAND-0001 to CAND-0100
    expected_pattern = re.compile(r'^CAND-\d{4}$')
    
    standard_candidates = []
    non_standard_candidates = []
    
    for candidate in candidates:
        candidate_id = candidate.get('candidate_id', 'MISSING_ID')
        if expected_pattern.match(candidate_id):
            standard_candidates.append(candidate)
        else:
            non_standard_candidates.append(candidate)
    
    print(f"\nStandard auto-generated candidates (CAND-XXXX): {len(standard_candidates)}")
    print(f"Non-standard or manually-added candidates: {len(non_standard_candidates)}")
    
    # Show non-standard candidates
    if non_standard_candidates:
        print("\n" + "=" * 70)
        print("NON-STANDARD CANDIDATES FOUND:")
        print("=" * 70)
        for candidate in non_standard_candidates:
            print(f"\nID: {candidate.get('candidate_id', 'MISSING')}")
            print(f"Name: {candidate.get('name', 'MISSING')}")
            print(f"Email: {candidate.get('email', 'MISSING')}")
            print(f"Education: {candidate.get('education', 'MISSING')}")
            print(f"Experience: {candidate.get('experience_years', 'MISSING')} years")
    else:
        print("\n✅ All candidates follow the standard auto-generated pattern (CAND-0001 to CAND-0100)")
    
    # Check for "Mia Singh" specifically
    print("\n" + "=" * 70)
    print("CHECKING FOR 'MIA SINGH':")
    print("=" * 70)
    
    mia_singh = None
    for candidate in candidates:
        if candidate.get('name', '').lower() == 'mia singh':
            mia_singh = candidate
            break
    
    if mia_singh:
        print("\n⚠️ 'Mia Singh' FOUND in candidates.json:")
        print(json.dumps(mia_singh, indent=2))
    else:
        print("\n❌ 'Mia Singh' NOT FOUND in candidates.json")
        print("This candidate must have been added from another source:")
        print("  - Uploaded via a custom script")
        print("  - Added through the UI (if upload feature exists)")
        print("  - Loaded from a different file")
        print("  - Entered manually in a test scenario")
    
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS:")
    print("=" * 70)
    print("1. If 'Mia Singh' appears in the dashboard, check session state")
    print("2. Look for temporary data files or cached session data")
    print("3. Check if there's a separate 'real_candidates.json' file")
    print("4. Verify if the dashboard allows manual candidate entry")
    
    return {
        'total': len(candidates),
        'standard': len(standard_candidates),
        'non_standard': len(non_standard_candidates),
        'mia_singh_found': mia_singh is not None,
        'non_standard_list': non_standard_candidates
    }


if __name__ == "__main__":
    result = check_candidates()
    
    if result['non_standard'] > 0 or not result['mia_singh_found']:
        print("\n⚠️ ACTION REQUIRED: Investigate data source discrepancy")
        exit(1)
    else:
        print("\n✅ All candidates verified as auto-generated")
        exit(0)
