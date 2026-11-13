from scripts.gen_erd import render

TABLES = {
    "users": {
        "description": "로그인 사용자",
        "columns": {
            "id": {"type": "integer", "primary_key": True},
            "username": {"type": "string", "length": 50, "unique": True},
        },
    },
    "posts": {
        "description": "게시글",
        "columns": {
            "id": {"type": "integer", "primary_key": True},
            "author_id": {"type": "integer", "foreign_key": "users.id", "ondelete": "CASCADE", "nullable": False},
            "editor_id": {"type": "integer", "foreign_key": "users.id", "ondelete": "SET NULL"},
        },
    },
    "profiles": {
        "description": "사용자 프로필 (1:1)",
        "columns": {
            "id": {"type": "integer", "primary_key": True},
            "user_id": {
                "type": "integer",
                "foreign_key": "users.id",
                "ondelete": "CASCADE",
                "nullable": False,
                "unique": True,
            },
        },
    },
}


def test_render_relations_follow_nullable_and_unique() -> None:
    """필수 FK 는 ||, 비어도 되는 FK 는 |o, unique FK 는 1:1(o|)"""
    content = render(TABLES)

    assert 'users ||--o{ posts : "author_id"' in content
    assert 'users |o--o{ posts : "editor_id"' in content
    assert 'users ||--o| profiles : "user_id"' in content


def test_render_columns_and_description_table() -> None:
    """컬럼에 PK·FK·UK 표시, 아래 표에 테이블 설명"""
    content = render(TABLES)

    assert "        integer id PK" in content
    assert "        string username UK" in content
    assert "        integer user_id FK, UK" in content
    assert "| `posts` | 게시글 |" in content
    assert content.startswith("# ERD")
