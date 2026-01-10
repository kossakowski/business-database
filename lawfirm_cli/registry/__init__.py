"""Registry enrichment module for KRS and CEIDG integration."""

from lawfirm_cli.registry.models import (
    RegistrySnapshot,
    NormalizedKRSProfile,
    NormalizedCEIDGProfile,
    NormalizedAddress,
    EnrichmentProposal,
    IdentifierProposal,
    ContactProposal,
    AddressProposal,
)

__all__ = [
    "RegistrySnapshot",
    "NormalizedKRSProfile", 
    "NormalizedCEIDGProfile",
    "NormalizedAddress",
    "EnrichmentProposal",
    "IdentifierProposal",
    "ContactProposal",
    "AddressProposal",
]
