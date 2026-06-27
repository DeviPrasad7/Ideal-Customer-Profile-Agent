"""
Data Transfer Objects (DTOs) for the ICP Agent platform.

These Pydantic models describe the shape of data exchanged between
agents and external services. Extracted from agent/utils.py to give
them a proper home in the models layer and prevent circular imports.
"""

from typing import Optional
from pydantic import BaseModel


class WebPage(BaseModel):
    """Scraped web page result returned by ScrapingService."""

    url: str
    htmlContent: str
    statusCode: int
    fetchTimeMs: int


class CompanyProfile(BaseModel):
    """Enriched company data from Crunchbase / LinkedIn."""

    name: str
    description: Optional[str] = None
    employeeCount: Optional[int] = None
    revenue: Optional[str] = None
    location: Optional[str] = None
    industries: list[str] = []


class TechStackEntry(BaseModel):
    """Single detected technology in a company's tech stack."""

    technology: str
    category: str
    confidence: float
    source: str


class JobPosting(BaseModel):
    """A job posting scraped from a careers page."""

    title: str
    department: str
    url: str
    postedDate: str


class EmailValidationResult(BaseModel):
    """Result of an email validation check."""

    email: str
    isValid: bool
    reason: str


class CompetitorMapping(BaseModel):
    """Competitor and pain-point mapping for a given technology."""

    technology: str
    competitors: list[str]
    painPoints: dict[str, str]
