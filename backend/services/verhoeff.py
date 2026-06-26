"""
Verhoeff Checksum Validator for Aadhaar numbers.
Every valid 12-digit Aadhaar passes this mathematical checksum.
"""

# Multiplication table (Cayley table of D5)
_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

# Permutation table
_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]

# Inverse table
_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]


def verhoeff_validate(number: str) -> bool:
    """
    Validates a number string using the Verhoeff checksum.
    Returns True if the number is valid.
    """
    c = 0
    for i, digit in enumerate(reversed(number)):
        c = _D[c][_P[i % 8][int(digit)]]
    return c == 0


def validate_aadhaar(aadhaar: str) -> dict:
    """
    Validates an Aadhaar number string.
    Returns dict with valid (bool), reason (str), and clean_number (str).
    """
    clean = aadhaar.replace(" ", "").replace("-", "").strip()

    if not clean.isdigit():
        return {"valid": False, "reason": "Contains non-digit characters", "clean_number": clean}

    if len(clean) != 12:
        return {"valid": False, "reason": f"Invalid length: {len(clean)} digits (expected 12)", "clean_number": clean}

    # First digit of Aadhaar must not be 0 or 1
    if clean[0] in ("0", "1"):
        return {"valid": False, "reason": "Aadhaar number cannot start with 0 or 1", "clean_number": clean}

    is_valid = verhoeff_validate(clean)
    return {
        "valid": is_valid,
        "reason": "Valid Aadhaar (checksum passed)" if is_valid else "Invalid Aadhaar (checksum failed)",
        "clean_number": clean,
    }
