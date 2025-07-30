from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class DateParts(BaseModel):
    date_parts: Optional[List[List[Optional[int]]]] = Field(None, alias='date-parts')

class Author(BaseModel):
    given: Optional[str] = None
    family: Optional[str] = None
    sequence: Optional[str] = None
    affiliation: Optional[List[Dict[str, Any]]] = None

class CrossrefWorkModel(BaseModel):
    DOI: str
    title: List[str]
    author: Optional[List[Author]] = None
    publisher: str
    type: str
    published_print: Optional[DateParts] = Field(None, alias='published-print')
    
    class Config:
        extra = 'allow' 
        populate_by_name = True