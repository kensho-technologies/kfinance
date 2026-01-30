from strenum import StrEnum


class Permission(StrEnum):
    CompetitorsPermission = "CompetitorsPermission"
    EarningsPermission = "EarningsPermission"
    GICSPermission = "GICSPermission"
    IDPermission = "IDPermission"
    ISCRSPermission = "ISCRSPermission"
    MergersPermission = "MergersPermission"
    PricingPermission = "PricingPermission"
    RelationshipPermission = "RelationshipPermission"
    SegmentsPermission = "SegmentsPermission"
    StatementsPermission = "StatementsPermission"
    TranscriptsPermission = "TranscriptsPermission"
    PrivateCompanyFinancialsPermission = "PrivateCompanyFinancialsPermission"
    CompanyIntelligencePermission = "CompanyIntelligencePermission"
    EstimatesPermission = "EstimatesPermission"
    # These permissions are not used by the client, but some users may have these permissions
    # Having them listed here will prevent an avoidable KeyError exception being logged.
    OnlyStaffPermission = "OnlyStaffPermission"
    PrivateCompanyFinancialsPermissionExcludeRedistribution = (
        "PrivateCompanyFinancialsPermissionExcludeRedistribution"
    )
