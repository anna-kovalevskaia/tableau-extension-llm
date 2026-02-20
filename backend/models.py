from pydantic import BaseModel
from typing import Union, List, Dict, Optional, Any

class SchemaRow(BaseModel):
    name: str
    type: str
    isDiscrete: bool

class FilterRow(BaseModel):
    filedName: str
    type: str
    values: Union[List[str], Dict[str, Any], None]

class Worksheet(BaseModel):
    worksheetName: str
    chunkField: Optional[str] = None
    schema: List[SchemaRow]
    filters: Optional[List[FilterRow]] = None

class Payload(BaseModel):
    question: str
    worksheet: Worksheet

class LLMResponseModel(BaseModel):
    required_fields: List[str]
    code: str
