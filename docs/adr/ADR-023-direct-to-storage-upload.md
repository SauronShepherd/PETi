# ADR-023: Direct-to-storage upload

The API creates and authorizes an upload session; media bytes are uploaded to the storage boundary and finalized through the API. The FastAPI process does not proxy large media.
