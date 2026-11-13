"""아키텍처 테스트 공용 — 위반 표현과 known-violations.json 래칫.

경계 테스트(test_boundary.py)와 스키마 테스트(test_schema.py)가 같은 기준선 파일을 공유한다.
각 테스트는 자기 규칙(rule prefix)에 해당하는 항목만 래칫 비교한다.
"""

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
KNOWN_VIOLATIONS_PATH = Path(__file__).with_name("known-violations.json")
RULES = ".claude/rules/backend"


@dataclass(frozen=True)
class Violation:
    """규칙 위반 1건"""

    file: str
    line: int
    rule: str
    detail: str
    rule_doc: str

    @property
    def key(self) -> str:
        """래칫 비교용 식별자 (줄 번호 제외 — 코드 이동에 흔들리지 않게)"""
        return f"{self.file}|{self.rule}|{self.detail}"

    def __str__(self) -> str:
        return f"VIOLATION: {self.file}:{self.line} [{self.rule}] {self.detail} — 수정 방법: {self.rule_doc} 참고"


def known_keys(owns_rule: Callable[[str], bool]) -> set[str]:
    """래칫 기준선 중 owns_rule 이 참인 규칙의 항목만"""
    entries = json.loads(KNOWN_VIOLATIONS_PATH.read_text(encoding="utf-8"))
    return {f"{entry['file']}|{entry['rule']}|{entry['detail']}" for entry in entries if owns_rule(entry["rule"])}


def new_violation_messages(violations: Iterable[Violation], owns_rule: Callable[[str], bool]) -> list[str]:
    """기준선에 없는 새 위반의 메시지 목록"""
    known = known_keys(owns_rule)
    return [str(violation) for violation in violations if violation.key not in known]


def stale_known_keys(violations: Iterable[Violation], owns_rule: Callable[[str], bool]) -> list[str]:
    """이미 고쳐졌는데 기준선에 남은 항목"""
    current = {violation.key for violation in violations}
    return sorted(known_keys(owns_rule) - current)


STALE_MESSAGE = (
    "이미 해결된 위반이 known-violations.json 에 남아 있다 — 해당 항목을 삭제하라 "
    "(목록은 줄어들 수만 있다, 새 항목 추가 금지):\n"
)
