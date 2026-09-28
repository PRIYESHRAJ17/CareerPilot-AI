from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ProviderDefinition:
    """
    Declarative definition of one job source.

    A definition describes how CareerPilot reaches a provider,
    how the response is interpreted, and what usage constraints
    apply.

    This keeps provider-specific configuration separate from
    adapter implementation.
    """

    name: str
    display_name: str

    adapter_type: str

    endpoint: str

    category: str = "job_board"

    countries: List[str] = field(
        default_factory=list
    )

    requires_credentials: bool = False

    credential_env_vars: List[str] = field(
        default_factory=list
    )

    method: str = "GET"

    headers: Dict[str, str] = field(
        default_factory=dict
    )

    static_params: Dict[str, Any] = field(
        default_factory=dict
    )

    query_parameter: Optional[str] = None

    location_parameter: Optional[str] = None

    limit_parameter: Optional[str] = None

    page_parameter: Optional[str] = None

    response_jobs_path: Optional[str] = None

    field_paths: Dict[str, str] = field(
        default_factory=dict
    )

    # Adapter-specific configuration.
    #
    # Examples:
    #
    # {
    #     "platform": "greenhouse",
    #     "board_token": "example"
    # }
    #
    # {
    #     "platform": "lever",
    #     "site": "example"
    # }
    adapter_config: Dict[str, Any] = field(
        default_factory=dict
    )

    salary_currency: Optional[str] = None

    remote_default: bool = False

    supports_paging: bool = True

    supports_remote_filter: bool = False

    supports_salary_filter: bool = False

    website: Optional[str] = None

    api_url: Optional[str] = None

    attribution_required: bool = False

    attribution_name: Optional[str] = None

    attribution_url: Optional[str] = None

    linkback_required: bool = False

    redistribution_restricted: bool = False

    enabled: bool = True

    tags: List[str] = field(
        default_factory=list
    )

    notes: Optional[str] = None

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        return {
            "name": self.name,

            "display_name": self.display_name,

            "adapter_type": self.adapter_type,

            "endpoint": self.endpoint,

            "category": self.category,

            "countries": list(
                self.countries
            ),

            "requires_credentials": (
                self.requires_credentials
            ),

            "credential_env_vars": list(
                self.credential_env_vars
            ),

            "method": self.method,

            "headers": dict(
                self.headers
            ),

            "static_params": dict(
                self.static_params
            ),

            "query_parameter": (
                self.query_parameter
            ),

            "location_parameter": (
                self.location_parameter
            ),

            "limit_parameter": (
                self.limit_parameter
            ),

            "page_parameter": (
                self.page_parameter
            ),

            "response_jobs_path": (
                self.response_jobs_path
            ),

            "field_paths": dict(
                self.field_paths
            ),

            "adapter_config": dict(
                self.adapter_config
            ),

            "salary_currency": (
                self.salary_currency
            ),

            "remote_default": (
                self.remote_default
            ),

            "supports_paging": (
                self.supports_paging
            ),

            "supports_remote_filter": (
                self.supports_remote_filter
            ),

            "supports_salary_filter": (
                self.supports_salary_filter
            ),

            "website": self.website,

            "api_url": self.api_url,

            "attribution_required": (
                self.attribution_required
            ),

            "attribution_name": (
                self.attribution_name
            ),

            "attribution_url": (
                self.attribution_url
            ),

            "linkback_required": (
                self.linkback_required
            ),

            "redistribution_restricted": (
                self.redistribution_restricted
            ),

            "enabled": self.enabled,

            "tags": list(
                self.tags
            ),

            "notes": self.notes,
        }