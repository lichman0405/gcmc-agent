from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests


class SemanticScholarClient:
    """
    Semantic Scholar API client based on official Graph API v1 documentation.
    
    References:
    - API Docs: https://api.semanticscholar.org/api-docs/graph
    - Python Client: https://github.com/danielnsilva/semanticscholar
    """
    
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.semanticscholar.org/graph/v1"):
        self.api_key = api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        if not self.api_key:
            # Unauthenticated use is possible but heavily rate-limited; encourage API key.
            print("[SemanticScholar] Warning: no API key set; unauthenticated requests may be rate-limited or rejected.")

    def search(
        self,
        query: str,
        limit: int = 5,
        year: str = None,
        fields_of_study: List[str] = None,
        open_access_pdf: bool = None,
        min_citation_count: int = None
    ) -> List[Dict[str, Any]]:
        """
        Search papers using relevance search endpoint.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            year: Year filter (e.g., "2020", "2015-2020", "2015-")
            fields_of_study: Filter by field (e.g., ["Chemistry", "Materials Science"])
            open_access_pdf: If True, only return papers with open access PDFs
            min_citation_count: Minimum citation count
            
        Returns:
            List of paper dictionaries
        """
        url = f"{self.base_url}/paper/search"
        headers = {"x-api-key": self.api_key} if self.api_key else {}
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,authors,year,venue,url,abstract,externalIds,citationCount,isOpenAccess,openAccessPdf,influentialCitationCount,publicationDate",
        }
        
        # Add optional filters
        if year:
            params["year"] = year
        if fields_of_study:
            params["fieldsOfStudy"] = ",".join(fields_of_study)
        if open_access_pdf is not None:
            params["openAccessPdf"] = str(open_access_pdf).lower()
        if min_citation_count is not None:
            params["minCitationCount"] = min_citation_count
        
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])

    def paper(self, paper_id: str) -> Dict[str, Any]:
        """
        Get detailed paper information.
        
        Args:
            paper_id: Semantic Scholar paper ID, DOI, or other supported ID
            
        Returns:
            Paper details dictionary
        """
        url = f"{self.base_url}/paper/{paper_id}"
        headers = {"x-api-key": self.api_key} if self.api_key else {}
        params = {
            "fields": "title,abstract,year,venue,authors,url,externalIds,citationCount,referenceCount,isOpenAccess,openAccessPdf,influentialCitationCount,publicationDate"
        }
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    
    def get_paper_citations(self, paper_id: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Get papers that cite this paper.
        
        Args:
            paper_id: Paper ID
            limit: Maximum number of citations
            offset: Pagination offset
            
        Returns:
            Dictionary with 'data' key containing list of citing papers
        """
        url = f"{self.base_url}/paper/{paper_id}/citations"
        headers = {"x-api-key": self.api_key} if self.api_key else {}
        params = {
            "fields": "title,year,authors,citationCount,isOpenAccess,paperId",
            "limit": limit,
            "offset": offset
        }
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    
    def get_paper_references(self, paper_id: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Get papers referenced by this paper.
        
        Args:
            paper_id: Paper ID
            limit: Maximum number of references
            offset: Pagination offset
            
        Returns:
            Dictionary with 'data' key containing list of referenced papers
        """
        url = f"{self.base_url}/paper/{paper_id}/references"
        headers = {"x-api-key": self.api_key} if self.api_key else {}
        params = {
            "fields": "title,year,authors,citationCount,isOpenAccess,openAccessPdf,paperId",
            "limit": limit,
            "offset": offset
        }
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    
    def get_papers_batch(self, paper_ids: List[str], fields: str = None) -> List[Dict[str, Any]]:
        """
        Get details for multiple papers in a single request (max 1000).
        
        Args:
            paper_ids: List of paper IDs (CorpusId, DOI, or paperId)
            fields: Comma-separated fields to include
            
        Returns:
            List of paper dictionaries
        """
        if len(paper_ids) > 1000:
            raise ValueError("Batch API supports max 1000 papers per request")
        
        url = f"{self.base_url}/paper/batch"
        headers = {"x-api-key": self.api_key} if self.api_key else {}
        
        if fields is None:
            fields = "title,year,authors,citationCount,abstract,externalIds"
        
        params = {"fields": fields}
        payload = {"ids": paper_ids}
        
        resp = requests.post(url, headers=headers, params=params, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()
