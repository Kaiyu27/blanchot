import re
from typing import Optional, Literal, List, Dict

from pydantic import BaseModel, ConfigDict, Field, model_validator

class Affiliation(BaseModel):
    raw_affiliation_string: str
    institution_ids: list[str]


class DehydratedAuthor(BaseModel):
    id: str
    display_name: str
    orcid: Optional[str] = None


class Institution(BaseModel):
    id: str
    display_name: str
    ror: str
    country_code: Optional[str]
    type: str
    lineage: list[str]


class Authorship(BaseModel):
    model_config = ConfigDict(extra='allow')
    affiliations: list[Affiliation]
    author: DehydratedAuthor
    author_position: Optional[Literal['first', 'middle', 'last']] = None


    # # TODO: see if there are standardized ways to represent a country
    countries: list[str]
    institutions: list[Institution]
    is_corresponding: Optional[bool] = None


class DehydratedSource(BaseModel):
    id: str
    display_name: str
    issn_l: Optional[str] = Field(pattern=r'^\d{4}-\d{3}[\dX]$')
    issn: Optional[list[str]]
    host_organization: Optional[str]
    type: Literal['journal', 'repository', 'conference', 'ebook platform', 'book series', 'metadata', 'other']

    # TODO: figure out how to validate
    @model_validator(mode='after')
    def validate_issn(self):
        issn_pattern = r'^\d{4}-\d{3}[\dX]$'
        
        if self.issn is not None:
            for id in self.issn:
                if not re.fullmatch(issn_pattern, id):
                    raise ValueError("Issn(s) formatted incorrectly")
        return self


class Location(BaseModel):
    is_oa: bool
    landing_page_url: Optional[str]
    pdf_url: Optional[str] = None
    source: Optional[DehydratedSource]
    license: Optional[str] = None
    version: Optional[Literal['publishedVersion', 'acceptedVersion', 'submittedVersion']] = None
    is_accepted: bool
    is_published: bool


#Top Level Model:
class OpenAlexWork(BaseModel):
    id: str
    doi: Optional[str] = None
    title: Optional[str]
    
    authorships: List[Authorship]
    primary_location: Optional[Location] = None
    locations: List[Location]

    type: str
    publication_date: str
    publication_year: int
    language: Optional[str] = None

    cited_by_count: int
    referenced_works: List[str]

    abstract_inverted_index: Optional[Dict[str, List[int]]] = None
    
    
    class Config:
        extra = 'allow'