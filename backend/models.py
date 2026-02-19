from pydantic import BaseModel
from typing import List, Optional, Any

class SchemaRow(BaseModel):
    name: str
    type: str
    isDiscrete: bool

class Worksheet(BaseModel):
    worksheetName: str
    chunkField: Optional[str]= None
    schema: List[SchemaRow]
    filters: Any

class Payload(BaseModel):
    question: str
    worksheet: Worksheet

class LLMResponseModel(BaseModel):
    required_fields: List[str]
    code: str
