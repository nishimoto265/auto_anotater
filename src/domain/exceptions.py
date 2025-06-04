"""
Domain層エラー定義 - Agent3専用
純粋ドメインロジックエラー・ビジネスルール違反検知
"""


class DomainError(Exception):
    """ドメイン層エラー基底クラス"""
    
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class ValidationError(DomainError):
    """
    検証エラー
    
    用途:
    - 座標範囲検証(0.0-1.0)
    - 個体ID検証(0-15)
    - 行動ID検証(0-4)
    - 信頼度検証(0.0-1.0)
    """
    
    def __init__(self, field_name: str, value, expected_range: str):
        message = f"Validation failed for {field_name}: {value} (expected: {expected_range})"
        super().__init__(message, "VALIDATION_ERROR")
        self.field_name = field_name
        self.value = value
        self.expected_range = expected_range


class BusinessRuleViolationError(DomainError):
    """
    ビジネスルール違反エラー
    
    用途:
    - 16個体上限違反
    - BB重複作成禁止
    - 座標系変換ルール違反
    - 追跡ルール違反
    """
    
    def __init__(self, rule_name: str, violation_details: str):
        message = f"Business rule violation: {rule_name} - {violation_details}"
        super().__init__(message, "BUSINESS_RULE_VIOLATION")
        self.rule_name = rule_name
        self.violation_details = violation_details


class EntityNotFoundError(DomainError):
    """
    エンティティ未発見エラー
    
    用途:
    - BB ID未発見
    - フレームID未発見
    - 個体ID未発見
    """
    
    def __init__(self, entity_type: str, entity_id: str):
        message = f"{entity_type} not found: {entity_id}"
        super().__init__(message, "ENTITY_NOT_FOUND")
        self.entity_type = entity_type
        self.entity_id = entity_id


class PerformanceError(DomainError):
    """
    パフォーマンス要件違反エラー
    
    用途:
    - IOU計算1ms超過
    - 座標変換0.5ms超過
    - エンティティ操作1ms超過
    """
    
    def __init__(self, operation: str, actual_time: float, target_time: float):
        message = f"Performance violation: {operation} took {actual_time}ms (target: {target_time}ms)"
        super().__init__(message, "PERFORMANCE_VIOLATION")
        self.operation = operation
        self.actual_time = actual_time
        self.target_time = target_time