"""Unit tests for Risk Detection engine."""

from app.domain.enums import RiskLevel
from app.risk_detection.engine import RiskDetectionEngine


class TestRiskDetectionEngine:
    def test_build_response_normalizes_levels(self) -> None:
        low = RiskDetectionEngine._build_response({"risk_level": "low", "reasoning": "ok", "recommended_action": "monitor"})
        assert low.risk_level == RiskLevel.LOW

        mod = RiskDetectionEngine._build_response({"risk_level": "medium", "reasoning": "x", "recommended_action": "y"})
        assert mod.risk_level == RiskLevel.MODERATE

        high = RiskDetectionEngine._build_response({"risk_level": "critical", "reasoning": "x", "recommended_action": "y"})
        assert high.risk_level == RiskLevel.HIGH

    def test_build_response_defaults_unknown_to_low(self) -> None:
        result = RiskDetectionEngine._build_response({"risk_level": "unknown"})
        assert result.risk_level == RiskLevel.LOW
