"""Permission resolution system for dynamic permission references in examples."""

from typing import List, Set, Dict, Any
import logging

logger = logging.getLogger(__name__)

try:
    from kfinance.client.permission_models import Permission
except ImportError:
    logger.warning("Could not import Permission model - using mock for development")
    from enum import Enum
    
    class Permission(Enum):
        StatementsPermission = "StatementsPermission"
        PricingPermission = "PricingPermission"
        EarningsPermission = "EarningsPermission"
        MergersPermission = "MergersPermission"
        CompanyIntelligencePermission = "CompanyIntelligencePermission"
        RelationshipPermission = "RelationshipPermission"
        SegmentsPermission = "SegmentsPermission"
        IDPermission = "IDPermission"
        CompetitorsPermission = "CompetitorsPermission"
        TranscriptsPermission = "TranscriptsPermission"


class PermissionResolver:
    """Resolves permission references to actual Permission enum values."""
    
    def __init__(self):
        """Initialize the permission resolver."""
        self.permission_mapping = {
            # Financial data permissions
            "STATEMENTS": Permission.StatementsPermission,
            "PRICING": Permission.PricingPermission,
            "EARNINGS": Permission.EarningsPermission,
            
            # Company data permissions
            "COMPANY_INTELLIGENCE": Permission.CompanyIntelligencePermission,
            "MERGERS": Permission.MergersPermission,
            "RELATIONSHIPS": Permission.RelationshipPermission,
            "SEGMENTS": Permission.SegmentsPermission,
            "COMPETITORS": Permission.CompetitorsPermission,
            
            # Identifier and utility permissions
            "ID": Permission.IDPermission,
            "TRANSCRIPTS": Permission.TranscriptsPermission,
            
            # Add missing mappings
            "RELATIONSHIP": Permission.RelationshipPermission,  # Handle both singular and plural
        }
    
    def resolve_permissions(self, permission_refs: List[str]) -> Set[Permission]:
        """
        Resolve permission reference strings to Permission enum values.
        
        Args:
            permission_refs: List of permission reference strings (e.g., ["STATEMENTS", "PRICING"])
            
        Returns:
            Set of Permission enum values
        """
        resolved_permissions = set()
        
        for ref in permission_refs:
            if ref in self.permission_mapping:
                resolved_permissions.add(self.permission_mapping[ref])
            else:
                # Try to resolve as direct Permission enum value
                try:
                    resolved_permissions.add(Permission(ref))
                except (ValueError, AttributeError):
                    logger.warning(f"Could not resolve permission reference: {ref}")
        
        return resolved_permissions
    
    def get_permission_reference(self, permission: Permission) -> str:
        """
        Get the reference string for a Permission enum value.
        
        Args:
            permission: Permission enum value
            
        Returns:
            Reference string for the permission
        """
        for ref, perm in self.permission_mapping.items():
            if perm == permission:
                return ref
        
        # Fallback to the permission value itself
        return permission.value
    
    def update_example_permissions(self, example_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update example data to use resolved permissions.
        
        Args:
            example_data: Example dictionary with permission references
            
        Returns:
            Updated example data with resolved permissions
        """
        if 'permissions_required' in example_data:
            permission_refs = example_data['permissions_required']
            resolved_permissions = self.resolve_permissions(permission_refs)
            # Convert back to list of permission values for JSON serialization
            example_data['permissions_required'] = [p.value for p in resolved_permissions]
        
        return example_data
    
    def get_available_permissions(self) -> Dict[str, str]:
        """
        Get mapping of permission references to their actual values.
        
        Returns:
            Dictionary mapping reference strings to permission values
        """
        return {ref: perm.value for ref, perm in self.permission_mapping.items()}


# Global resolver instance
_resolver = None

def get_permission_resolver() -> PermissionResolver:
    """Get the global permission resolver instance."""
    global _resolver
    if _resolver is None:
        _resolver = PermissionResolver()
    return _resolver


def resolve_permissions(permission_refs: List[str]) -> Set[Permission]:
    """Convenience function to resolve permissions."""
    return get_permission_resolver().resolve_permissions(permission_refs)


if __name__ == "__main__":
    # Test the resolver
    resolver = PermissionResolver()
    
    test_refs = ["STATEMENTS", "PRICING", "COMPANY_INTELLIGENCE"]
    resolved = resolver.resolve_permissions(test_refs)
    
    print("Permission References:")
    for ref in test_refs:
        print(f"  {ref} -> {resolver.permission_mapping.get(ref)}")
    
    print(f"\nResolved Permissions: {resolved}")
    
    print(f"\nAvailable Permissions:")
    for ref, value in resolver.get_available_permissions().items():
        print(f"  {ref}: {value}")
