import argparse
import json
import sys


def validate_attestation(data, subject_name, subject_digest, commit):
    """
    Validates the attestation verification JSON.

    Args:
        data (dict): The parsed JSON data from `gh attestation verify`.
        subject_name (str): The expected subject name.
        subject_digest (str): The expected subject digest (sha256).
        commit (str): The expected git commit SHA.

    Returns:
        int: 0 if valid, 1 otherwise.
    """
    if not isinstance(data, list) or len(data) != 1:
        print("ERROR: Expected a JSON array with a single element.", file=sys.stderr)
        return 1

    verification_result = data[0].get("verificationResult")
    if not verification_result:
        print("ERROR: Missing 'verificationResult'.", file=sys.stderr)
        return 1

    statement = verification_result.get("statement")
    if not statement:
        print("ERROR: Missing 'statement'.", file=sys.stderr)
        return 1

    # Validate subject
    subjects = statement.get("subject")
    if not isinstance(subjects, list) or len(subjects) != 1:
        print("ERROR: Expected exactly one subject.", file=sys.stderr)
        return 1
    
    subject = subjects[0]
    if subject.get("name") != subject_name:
        print(f"ERROR: Subject name mismatch. Expected {subject_name}, got {subject.get('name')}", file=sys.stderr)
        return 1
    
    digest = subject.get("digest", {}).get("sha256")
    if digest != subject_digest:
        print(f"ERROR: Subject digest mismatch. Expected {subject_digest}, got {digest}", file=sys.stderr)
        return 1

    # Validate commit in resolvedDependencies
    try:
        resolved_deps = statement["predicate"]["buildDefinition"]["resolvedDependencies"]
        found_commit = False
        if isinstance(resolved_deps, list):
            for dep in resolved_deps:
                if dep.get("digest", {}).get("gitCommit") == commit:
                    found_commit = True
                    break
        if not found_commit:
            print(f"ERROR: Expected commit {commit} not found in resolvedDependencies.", file=sys.stderr)
            return 1
    except (KeyError, TypeError) as e:
        print(f"ERROR: Could not resolve commit in predicate: {e}", file=sys.stderr)
        return 1

    print("SUCCESS: Attestation validation passed.", file=sys.stderr)
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate attestation verification JSON.")
    parser.add_argument("--input", required=True, help="Path to the verification JSON file.")
    parser.add_argument("--subject-name", required=True, help="Expected subject name.")
    parser.add_argument("--subject-digest", required=True, help="Expected subject digest (sha256).")
    parser.add_argument("commit", help="Expected git commit SHA.")
    
    args = parser.parse_args()

    try:
        with open(args.input) as f:
            attestation_data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"ERROR: Failed to read or parse input file: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(validate_attestation(attestation_data, args.subject_name, args.subject_digest, args.commit))
