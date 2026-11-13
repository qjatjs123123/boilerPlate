"""테이블 간 스키마 검사(test_schema.py 의 중복 의심·미사용)가 실제로 잡고, 사유가 있으면 넘어가는지 확인한다."""

from pathlib import Path

from sqlalchemy import Column, DateTime, ForeignKey, Integer, MetaData, String, Table

from tests.architecture.test_schema import (
    DesignedTable,
    TableSource,
    _app_referenced_names,
    _check_similar_tables,
    _check_unused_tables,
    _validate_design_table,
)


def _behavior_table(metadata: MetaData, name: str, extra: list[Column] | None = None) -> Table:
    """posts·users 를 가리키는 '사용자 행동' 모양 테이블 (좋아요·북마크 같은)"""
    return Table(
        name,
        metadata,
        Column("id", Integer, primary_key=True),
        Column("post_id", ForeignKey("posts.id", ondelete="CASCADE")),
        Column("user_id", ForeignKey("users.id", ondelete="CASCADE")),
        Column("created_at", DateTime),
        Column("updated_at", DateTime),
        *(extra or []),
    )


def _metadata_with_behaviors(*names: str) -> tuple[MetaData, dict[str, Table]]:
    """users·posts + 행동 테이블들"""
    metadata = MetaData()
    Table("users", metadata, Column("id", Integer, primary_key=True))
    Table("posts", metadata, Column("id", Integer, primary_key=True))
    return metadata, {name: _behavior_table(metadata, name) for name in names}


def _designed(name: str, distinct_from: dict[str, str] | None = None) -> DesignedTable:
    return DesignedTable(
        name=name, description=name, is_association=False, columns={}, distinct_from=distinct_from or {}
    )


def test_similar_tables_flagged() -> None:
    """같은 모양의 좋아요·북마크 테이블은 중복 의심으로 잡힌다"""
    _, tables = _metadata_with_behaviors("post_bookmarks", "post_likes")

    violations = _check_similar_tables(tables, {}, {})

    assert [violation.rule for violation in violations] == ["schema-similar-tables"]
    assert "post_likes: post_bookmarks 와 모양이 거의 같음" in violations[0].detail


def test_similar_tables_pass_with_distinct_reason() -> None:
    """어느 한쪽에 distinct_from 사유가 있으면 통과"""
    _, tables = _metadata_with_behaviors("post_bookmarks", "post_likes")
    design = {"post_likes": _designed("post_likes", {"post_bookmarks": "좋아요는 공개 집계, 북마크는 본인만 봄"})}

    assert _check_similar_tables(tables, design, {}) == []


def test_different_shape_not_flagged() -> None:
    """FK 대상이 같아도 컬럼 구성이 다르면 잡지 않는다 (댓글 vs 좋아요)"""
    metadata, tables = _metadata_with_behaviors("post_likes")
    tables["comments"] = _behavior_table(
        metadata, "comments", [Column("content", String(500)), Column("parent_id", Integer)]
    )

    assert _check_similar_tables(tables, {}, {}) == []


def test_empty_distinct_reason_is_design_violation() -> None:
    """distinct_from 사유를 비워 두면 설계 형식 위반"""
    violations = _validate_design_table(_designed("post_likes", {"post_bookmarks": " "}))

    assert [violation.rule for violation in violations] == ["schema-data-model-invalid"]


def test_unused_table_flagged_and_used_passes() -> None:
    """모델 클래스를 아무 데서도 안 쓰면 잡고, 쓰면 통과"""
    sources = {
        "posts": TableSource("app/domains/post/models.py", 1, "Post"),
        "reports": TableSource("app/domains/report/models.py", 1, "Report"),
    }

    violations = _check_unused_tables({}, sources, referenced={"Post", "select"})

    assert [violation.detail.split(":")[0] for violation in violations] == ["reports"]


def test_association_table_never_unused() -> None:
    """연결 테이블은 relationship 이 쓰므로 미사용 검사에서 제외"""
    sources = {"post_tag": TableSource("app/domains/post/models.py", 1, "PostTag")}
    design = {"post_tag": DesignedTable("post_tag", "연결", is_association=True, columns={})}

    assert _check_unused_tables(design, sources, referenced=set()) == []


def test_referenced_names_include_string_relationship(tmp_path: Path) -> None:
    """relationship("Report") 처럼 문자열로만 써도 참조로 본다, 클래스 정의 자체는 참조가 아니다"""
    (tmp_path / "models.py").write_text('class Report:\n    pass\n\nowner = relationship("Report")\n', encoding="utf-8")
    (tmp_path / "other.py").write_text("class Unused:\n    pass\n", encoding="utf-8")

    referenced = _app_referenced_names(tmp_path)

    assert "Report" in referenced
    assert "Unused" not in referenced
