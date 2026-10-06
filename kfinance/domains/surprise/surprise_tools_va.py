from kfinance.integrations.tool_calling.tool_calling_models import ToolRespWithIdInfoAndErrors


class GetVaSurpriseFromIdentifiersResp(ToolRespWithIdInfoAndErrors[VisibleAlphaSurprises]):
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, AlternativeLineItemMetadata] = Field(default_factory=dict)
    data_source: str
