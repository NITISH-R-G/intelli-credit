from pydantic import BaseModel, Field

class BankStatementData(BaseModel):
    """Strictly typed expectations for bank statement CSV extraction algorithms."""
    model_config = {"extra": "allow"}
    average_balance: float = Field(default=0.0)
    monthly_inflow: float = Field(default=0.0)
    monthly_outflow: float = Field(default=0.0)
    bounce_count: int = Field(default=0)
    utilization_rate: float = Field(default=0.0)
    trend: str = Field(default="Stable")

class BureauData(BaseModel):
    """Strictly typed definitions for integrated credit bureau JS payloads."""
    model_config = {"extra": "allow"}
    bureau_score: int = Field(default=700)
    active_tradelines: int = Field(default=0)
    total_inquiries_30d: int = Field(default=0)
    dpd_history: str = Field(default="000")
    credit_history_months: int = Field(default=60)
    total_exposure: float = Field(default=0.0)

class FinancialPDFData(BaseModel):
    """Strictly typed schema defining parameters extracted from parsed PNL & BS documents."""
    model_config = {"extra": "allow"}
    revenue: float = Field(default=0.0)
    net_income: float = Field(default=0.0)
    total_assets: float = Field(default=0.0)
    total_liabilities: float = Field(default=0.0)
    total_debt: float = Field(default=0.0)
    current_assets: float = Field(default=0.0)
    current_liabilities: float = Field(default=0.0)
    total_equity: float = Field(default=0.0)
