"""
Alias mining script
-------------------
Reads `entity_miss` events from `chatbi_audit.log`, counts high-frequency unmatched
phrases, and automatically generates the most likely mapping suggestion for each
candidate.

Usage:
    # Show suggestions only
    python scripts/mine_aliases.py [--log chatbi_audit.log] [--top 30]

    # Confirm interactively and write to the dictionary
    python scripts/mine_aliases.py --apply
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

NORMALIZER_PATH = Path(__file__).parent.parent / "db_mcp_server" / "entity_normalizer.py"


def load_misses(log_path: Path) -> tuple[list[str], list[dict]]:
    """Extract all unmatched phrases and low-confidence records from the audit log."""
    unmatched_all: list[str] = []
    low_conf_all: list[dict] = []

    with log_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("event") != "entity_miss":
                continue
            unmatched_all.extend(record.get("unmatched", []))
            low_conf_all.extend(record.get("low_confidence", []))

    return unmatched_all, low_conf_all


def suggest_mapping(phrase: str, entity_map: dict, embed_model) -> tuple[str, str, float]:
    """Suggest the best mapping for a candidate phrase using fuzzy matching and embeddings.
    Returns (key_to_add, suggested_value, confidence).
    For multi-word phrases, try 2-gram/3-gram subphrases first so we do not add
    entire long sentences into the dictionary.
    """
    from rapidfuzz import fuzz, process as fuzz_process

    entity_keys = list(entity_map.keys())
    tokens = phrase.split()

    # Candidate keys: try short subphrases first (2-gram / 3-gram), then the full phrase.
    candidates_to_try: list[str] = []
    if len(tokens) > 2:
        for span_len in range(2, min(4, len(tokens))):
            for start in range(len(tokens) - span_len + 1):
                candidates_to_try.append(" ".join(tokens[start:start + span_len]))
    candidates_to_try.append(phrase)

    best_key_phrase = phrase
    best_value: str | None = None
    best_score = 0.0

    for candidate in candidates_to_try:
        result = fuzz_process.extractOne(
            candidate.lower(), entity_keys,
            scorer=fuzz.token_set_ratio, score_cutoff=60,
        )
        if result:
            matched_key, score, _ = result
            if score > best_score:
                best_score = score
                best_key_phrase = candidate
                best_value = entity_map[matched_key]["name"]

    if best_value:
        return best_key_phrase, best_value, round(best_score / 100, 3)

    import numpy as np
    phrase_vec = embed_model.encode([phrase], normalize_embeddings=True)
    all_vecs   = embed_model.encode(list(entity_map.keys()), normalize_embeddings=True)
    scores     = (all_vecs @ phrase_vec.T).flatten()
    best_idx   = int(np.argmax(scores))
    return phrase, entity_map[entity_keys[best_idx]]["name"], round(float(scores[best_idx]), 3)


def detect_dict_type(original: str, suggested: str, entity_map: dict) -> str:
    """Decide whether the mapping belongs in ABBREV_MAP or METRIC_ABBREV_MAP."""
    from db_mcp_server.entity_normalizer import METRIC_ABBREV_MAP
    if suggested in METRIC_ABBREV_MAP.values():
        return "METRIC_ABBREV_MAP"
    if suggested.lower() in entity_map:
        return "ABBREV_MAP"
    return "ABBREV_MAP"


def append_to_dict(original: str, suggested: str, dict_name: str) -> bool:
    """Append original -> suggested to the end of the target dictionary in entity_normalizer.py."""
    src = NORMALIZER_PATH.read_text(encoding="utf-8")

    # Find the target dictionary's closing brace and insert the new entry before it.
    pattern = rf'({re.escape(dict_name)}.*?)(^\}})'
    # Simple approach: locate the dictionary and insert before its closing brace.
    dict_start = src.find(f"{dict_name}:")
    if dict_start == -1:
        print(f"  x Could not find {dict_name}")
        return False

    # Find the closing brace of the dictionary.
    brace_depth = 0
    insert_pos  = -1
    for i in range(dict_start, len(src)):
        if src[i] == "{":
            brace_depth += 1
        elif src[i] == "}":
            brace_depth -= 1
            if brace_depth == 0:
                insert_pos = i
                break

    if insert_pos == -1:
        print(f"  x Could not locate the closing brace for {dict_name}")
        return False

    # Check whether the entry already exists.
    if f'"{original}"' in src[dict_start:insert_pos] or f"'{original}'" in src[dict_start:insert_pos]:
        print(f"  i '{original}' is already present in {dict_name}")
        return False

    new_entry = f'    "{original}": "{suggested}",  # auto-mined\n'
    new_src   = src[:insert_pos] + new_entry + src[insert_pos:]
    NORMALIZER_PATH.write_text(new_src, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(description="Mine alias candidates from audit log")
    parser.add_argument("--log",   default="chatbi_audit.log", help="Path to audit log")
    parser.add_argument("--top",   type=int, default=30, help="Top N candidates to show")
    parser.add_argument("--apply", action="store_true", help="Interactive: confirm and write to dictionary")
    args = parser.parse_args()

    log_path = Path(args.log)
    if not log_path.exists():
        print(f"Log file not found: {log_path}")
        sys.exit(1)

    unmatched_all, low_conf_all = load_misses(log_path)
    if not unmatched_all and not low_conf_all:
        print("No entity_miss events found in log.")
        return

    unmatched_counter = Counter(p.lower() for p in unmatched_all)
    low_conf_counter  = Counter(r["phrase"].lower() for r in low_conf_all)
    combined: Counter = Counter()
    for phrase, cnt in unmatched_counter.items():
        combined[phrase] += cnt * 2
    for phrase, cnt in low_conf_counter.items():
        combined[phrase] += cnt

    top_candidates = combined.most_common(args.top)
    if not top_candidates:
        print("No candidates found.")
        return

    print("Loading models...")
    from db_mcp_server.entity_normalizer import EntityNormalizer
    normalizer = EntityNormalizer()

    if not args.apply:
        print(f"\n{'Freq':>4}  {'Original Phrase':<20}  {'Suggested Mapping':<30}  {'Conf':>6}")
        print("-" * 70)
        for phrase, count in top_candidates:
            _, suggested, conf = suggest_mapping(phrase, normalizer.entity_map, normalizer.embed_model)
            flag = "⚠️ " if conf < 0.70 else "  "
            print(f"{count:>4}  {phrase:<20}  → {suggested:<28}  {conf:>6.3f} {flag}")
        print("\nUse --apply to enter interactive mode, confirm suggestions, and write them to the dictionary.")
        return

    # --apply interactive mode
    print("\nReview suggestions one by one. Enter y to write, n to skip, or q to quit.\n")
    added = 0
    for phrase, count in top_candidates:
        _, suggested, conf = suggest_mapping(phrase, normalizer.entity_map, normalizer.embed_model)
        dict_name = detect_dict_type(phrase, suggested, normalizer.entity_map)
        flag = " WARNING: low confidence, please review manually" if conf < 0.70 else ""
        print(f"[{count}x]  '{phrase}'  ->  '{suggested}'  (conf={conf:.3f}, write to {dict_name}){flag}")

        while True:
            ans = input("  Add to dictionary? [y/n/q] ").strip().lower()
            if ans in ("y", "n", "q"):
                break

        if ans == "q":
            break
        if ans == "n":
            print("  Skipped")
            continue

        # Let the user override the suggested mapping.
        custom = input(f"  Mapping value (press Enter to accept '{suggested}'): ").strip()
        final_suggested = custom if custom else suggested

        ok = append_to_dict(phrase, final_suggested, dict_name)
        if ok:
            print(f"  ✓ Written to {dict_name}: '{phrase}' -> '{final_suggested}'")
            added += 1

    print(f"\nDone. Added {added} entries in total. Restart the service for changes to take effect.")


if __name__ == "__main__":
    main()
