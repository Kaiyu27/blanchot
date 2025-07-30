from typing import List, Optional
from pydantic import BaseModel, HttpUrl

class HALWorkModel(BaseModel):
    title_s: List[str]
    docType_s: str
    uri_s: HttpUrl
    authFullName_s: Optional[List[str]] = None
    publicationDateY_i: Optional[int] = None
    journalTitle_s: Optional[str] = None
    class Config:
        extra = 'allow'