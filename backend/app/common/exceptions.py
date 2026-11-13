class AppException(Exception):
    """도메인 예외 베이스 — 글로벌 핸들러가 envelope로 변환한다"""

    status_code: int = 500
    message: str = "일시적인 오류가 발생했습니다."

    def __init__(
        self,
        message: str | None = None,
        fields: dict[str, list[str]] | None = None,
    ) -> None:
        self.message = message or self.__class__.message
        self.fields = fields or {}
        super().__init__(self.message)
