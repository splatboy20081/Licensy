import string
import secrets
from typing import List


class LicenseFormatter:
    """
    'D' meaning digit, represents digit
    'U' meaning uppercase, represents uppercase english alphabet letter
    'L' meaning lowercase, represents lowercase english alphabet letter
    'A' meaning all, represents both uppercase and lowercase english alphabet letter + digits (without symbols!)
    'S' meaning symbol, represents symbols (punctuation symbols)

    So example format can be "DDDD-UUUU-LLLL-ULDS" which would generate:
    "4739-EHZB-fhgt-Qp1*"
    "7380-ODHJ-hfpm-Wc8!"
    etc

    If the license has branding it needs to be marked with "{branding}"
    """

    default_license_format = "{branding}AAAAA-AAAAA-AAAAA-AAAAA-AAAAA"
    min_permutation_count = 10**24
    min_license_length = 14
    _mapping = {
        "D": string.digits,
        "U": string.ascii_uppercase,
        "L": string.ascii_lowercase,
        "A": string.ascii_letters + string.digits,
        "S": string.punctuation
    }
    _possible_chars = set(char for char in _mapping.values())

    @classmethod
    def parse_format(cls, license_format: str, branding: str) -> str:
        if not license_format:
            license_format = cls.default_license_format

        license_format_split = license_format.split("{branding}")
        temp = []

        for i, split in enumerate(license_format_split):
            temp.append([])
            for char in split:
                if (charset := cls._mapping.get(char)) is not None:
                    temp[i].append(secrets.choice(charset))
                else:
                    temp[i].append(char)

        built_string = ["".join(sublist) if len(sublist) > 0 else "{branding}" for sublist in temp]
        built_string = "".join(built_string)
        return built_string.format(branding=branding)

    @classmethod
    def generate_single(cls, license_format: str, branding: str) -> str:
        return cls.parse_format(license_format, branding)

    @classmethod
    def generate_multiple(cls, license_format: str, branding: str, amount: int) -> List[str]:
        return [cls.generate_single(license_format, branding) for _ in range(amount)]

    @classmethod
    def is_secure(cls, license_format: str) -> bool:
        if len(license_format) < cls.min_license_length:
            return False

        permutations = cls.get_format_permutations(license_format)
        return permutations >= cls.min_permutation_count

    @classmethod
    def get_format_permutations(cls, license_format: str) -> int:
        permutations = 1
        license_format = license_format.replace("{branding}", "")
        for char in license_format:
            if charset := cls._mapping.get(char):
                permutations *= len(charset)

        return permutations
