# Copyright: 2022, ECP, NLnet Labs and the Internet.nl contributors
# SPDX-License-Identifier: Apache-2.0
from pyparsing import (
    CaselessLiteral,
    Combine,
    Literal,
    Group,
    OneOrMore,
    ParseException,
    ParserElement,
    Regex,
    StringEnd,
    Word,
    LineEnd,
    Optional,
    nums
)

ParserElement.setDefaultWhitespaceChars("")

# Parser for MTA-STS policies.
#
# The policy is parsed based on the RFC-8461 specifications of MTA-STS.
#
# The policy can have:
# - One mandatory "version" and it has to be "STSv1".
# - One mandatory "mode" and it has to be one of "enforce", "testing", or "none".
# - One mandatory "max_age" that is a plaintext non-negative integer seconds, maximum value of 31557600.
# - One or more "mx"  (example: mx: mail.example.com <CRLF>      mx: *.example.net)
#

# Define the grammar
# Define literals
equal = Literal("=")
colon = Literal(":") + Optional(" ")
version_literal = CaselessLiteral("version")
mode_literal = CaselessLiteral("mode")
max_age_literal = CaselessLiteral("max_age")
mx_literal = CaselessLiteral("mx")
newline = Optional("\r") + LineEnd()


# Define possible values
version_value = Literal("STSv1")
mode_values = CaselessLiteral("enforce") | CaselessLiteral("testing") | CaselessLiteral("none")
max_age_value = Word(nums).setParseAction(lambda tokens: int(tokens[0]) if 0 <= int(tokens[0]) <= 31557600 else None)

# validate mx values
def _parse_mx_pattern(tokens):
    mx_pattern = tokens[0]
    if mx_pattern.startswith("*."):
        return mx_pattern[2:]  # remove the '*.' for wildcard domains
    return mx_pattern

mx_value = Regex(r"[^\s]+").setParseAction(_parse_mx_pattern)

version = Combine(version_literal + colon + version_value)("version")
mode = Combine(mode_literal + colon + mode_values)("mode")
max_age = Combine(max_age_literal + colon + max_age_value)("max_age")
mx = Combine(mx_literal + colon + mx_value)("mx")

policy = (
    Group(version + newline) +
    Group(mode + newline) +
    OneOrMore(Group(mx + newline)) +
    Group(max_age + newline) +
    StringEnd()
)

def parse(mtasts_policy):
    try:
        parsed = policy.parseString(mtasts_policy)
    except ParseException as e:
        print(e)
        parsed = None
    except Exception as e:
        print(f"{e.__class__.__name__}: {e}")
        parsed = None
    return parsed
