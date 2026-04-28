# MPA Oceans-X MCP Server Implementation Plan

This document provides a detailed implementation plan for building a Python MCP server that wraps the Maritime and Port Authority (MPA) of Singapore Oceans-X APIs as MCP tools.

---

## Table of Contents

1. [Overview](#1-overview)
2. [MCP Tools Specification](#2-mcp-tools-specification)
   - [Schedule Category](#21-schedule-category)
   - [Port Category](#22-port-category)
   - [Port Clearance Category](#23-port-clearance-category)
   - [Vessel Info Category](#24-vessel-info-category)
3. [Shared Utilities](#3-shared-utilities)
4. [File Structure](#4-file-structure)
5. [Environment Variables](#5-environment-variables)
6. [Authentication Flow](#6-authentication-flow)
7. [Deployment to Azure Container Apps](#7-deployment-to-azure-container-apps)
8. [Implementation Notes](#8-implementation-notes)

---

## 1. Overview

**Goal:** Build a FastMCP server that exposes 17 MCP tools corresponding to 17 MPA Oceans-X API endpoints across 4 categories.

**Technical Stack:**
- **Framework:** FastMCP (Python)
- **Transport:** Streamable HTTP (`StreamableHttpTransport`)
- **HTTP Client:** `httpx` (async)
- **Validation:** Pydantic models with regex/length constraints
- **Deployment:** Azure Container Apps

**Key Requirements:**
- Forward `apikey` header from MCP client to upstream MPA APIs
- Validate all input parameters before making upstream requests
- Return structured JSON responses with consistent error handling
- Support all 17 endpoints across 4 categories

---

## 2. MCP Tools Specification

### 2.1 Schedule Category

#### Tool 1: `get_vessel_arrivals_by_date`
- **Description:** Get vessel arrivals for a specific date
- **Upstream URL:** `https://oceans-x.mpa.gov.sg/api/v1/vessel/arrivals/1.0.0/date/{date}`
- **HTTP Method:** `GET`
- **Parameters:**
  | Name | Type | Required | Validation | Description |
  |------|------|----------|------------|-------------|
  | `date` | `string` | Yes | Regex: `^\d{4}-\d{2}-\d{2}$` | Date in yyyy-MM-dd format |
- **Response:** Array of vessel arrivals with vesselParticulars, arrivedTime, locationFrom, locationTo

---

#### Tool 2: `get_vessel_departures_past_hours`
- **Description:** Get vessel departures for past N hours from a given datetime
- **Upstream URL:** `https://oceans-x.mpa.gov.sg/api/v1/vessel/departure/1.0.0/date/{datetime}/hours/{hours}`
- **HTTP Method:** `GET`
- **Parameters:**
  | Name | Type | Required | Validation | Description |
  |------|------|----------|------------|-------------|
  | `datetime` | `string` | Yes | Regex: `^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$` | Start datetime (yyyy-MM-dd HH:mm:ss) |
  | `hours` | `string` | Yes | Regex: `^[\d]{1,2}(\.\d{1,2})?$` | Number of hours to look back (1-99, optional decimal) |
- **Response:** Array of vessel departures with vesselParticulars, departedTime

---

#### Tool 3: `get_vessels_due_to_depart_next_hours`
- **Description:** Get vessels due to depart for next N hours from a given datetime
- **Upstream URL:** `https://oceans-x.mpa.gov.sg/api/v1/vessel/duetodepart/1.0.0/date/{datetime}/hours/{hours}`
- **HTTP Method:** `GET`
- **Parameters:**
  | Name | Type | Required | Validation | Description |
  |------|------|----------|------------|-------------|
  | `datetime` | `string` | Yes | Regex: `^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$` | Start datetime (yyyy-MM-dd HH:mm:ss) |
  | `hours` | `string` | Yes | Regex: `^[\d]{1,2}(\.\d{1,2})?$` | Number of hours to look ahead |
- **Response:** Array of vessels with vesselParticulars, dueToDepart

---

#### Tool 4: `get_vessels_due_to_arrive_by_date`
- **Description:** Get vessels due to arrive for a specific date
- **Upstream URL:** `https://oceans-x.mpa.gov.sg/api/v1/vessel/duetoarrive/1.0.0/date/{date}`
- **HTTP Method:** `GET`
- **Parameters:**
  | Name | Type | Required | Validation | Description |
  |------|------|----------|------------|-------------|
  | `date` | `string` | Yes | Regex: `^\d{4}-\d{2}-\d{2}$` | Date in yyyy-MM-dd format |
- **Response:** Array of vessels with vesselParticulars, duetoArriveTime, locationFrom, locationTo

---

#### Tool 5: `get_vessels_due_to_arrive_next_hours`
- **Description:** Get vessels due to arrive for next N hours from a given datetime
- **Upstream URL:** `https://oceans-x.mpa.gov.sg/api/v1/vessel/duetoarrive/1.0.0/date/{date}/hours/{hours}`
- **HTTP Method:** `GET`
- **Parameters:**
  | Name | Type | Required | Validation | Description |
  |------|------|----------|------------|-------------|
  | `datetime` | `string` | Yes | Regex: `^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$` | Start datetime (yyyy-MM-dd HH:mm:ss) |
  | `hours` | `string` | Yes | Regex: `^[\d]{1,2}(\.\d{1,2})?$` | Number of hours to look ahead |
- **Response:** Array of vessels with vesselParticulars, duetoArriveTime, locationFrom, locationTo

---

### 2.2 Port Category

#### Tool 6: `get_country_codes`
- **Description:** Get country codes reference data in JSON format
- **Upstream URL:** `https://oceans-x.mpa.gov.sg/api/v1/mdhvessel/reference/countries/1.0.0/filetype/json`
- **HTTP Method:** `GET`
- **Parameters:** None
- **Response:** Array of country codes with nationality, timeStamp, countryCode, countryDescription

---

#### Tool 7: `get_vessel_movements_by_callsign`
- **Description:** Get vessel movements by call sign
- **Upstream URL:** `https://oceans-x.mpa.gov.sg/api/v1/vessel/movements/1.0.0/callsign/{callsign}`
- **HTTP Method:** `GET`
- **Parameters:**
  | Name | Type | Required | Validation | Description |
  |------|------|----------|------------|-------------|
  | `callsign` | `string` | Yes | Regex: `^[a-zA-Z0-9]+$`, Length: 1-8 | Call sign of the vessel |
- **Response:** Array of movements with vesselParticulars, movementStartDateTime, movementEndDateTime, movementStatus, movementType, locationFrom, locationTo, movementDraft, movementHeight

---

#### Tool 8: `get_vessel_positions_snapshot`
- **Description:** Get a snapshot of all vessel positions
- **Upstream URL:** `https://oceans-x.mpa.gov.sg/api/v1/vessel/positions/1.0.0/snapshot`
- **HTTP Method:** `GET`
- **Parameters:** None
- **Response:** Array of vessel positions with vesselParticulars (including extended fields), latitude, longitude, latitudeDegrees, longitudeDegrees, speed, course, heading, dimA, dimB, timeStamp

---

#### Tool 9: `get_vessel_positions_by_imo`
- **Description:** Get vessel positions by IMO number
- **Upstream URL:** `https://oceans-x.mpa.gov.sg/api/v1/vessel/positions/1.0.0/imonumber/{imonumber}`
- **HTTP Method:** `GET`
- **Parameters:**
  | Name | Type | Required | Validation | Description |
  |------|------|----------|------------|-------------|
  | `imonumber` | `string` | Yes | Regex: `^[a-zA-Z0-9]+$`, Length: 1-10 | IMO number of the vessel |
- **Response:** Array of vessel positions with full details

---

### 2.3 Port Clearance Category

#### Tool 10: `get_vessel_arrival_declaration_latest_by_name`
- **Description:** Get latest vessel arrival declaration by vessel name
- **Upstream URL:** `https://oceans-x.mpa.gov.sg/api/v1/vessel/arrivaldeclaration/1.0.0/last/vesselname/{vesselname}`
- **HTTP Method:** `GET`
- **Parameters:**
  | Name | Type | Required | Validation | Description |
  |------|------|----------|------------|-------------|
  | `vesselname` | `string` | Yes | Regex: `^[0-9a-zA-Z-_. ']+$`, Length: 1-35 | Name of the vessel |
- **Response:** Array of declarations with vesselParticulars, location, grid, purpose, agent, reportedArrivalTime, crew, pax

---

#### Tool 11: `get_port_clearance_certificate_by_imo`
- **Description:** Get port clearance certificate by IMO number, GDV number, and certificate number
- **Upstream URL:** `https://oceans-x.mpa.gov.sg/api/v1/vessel/portclearance/1.0.0/imonumber/{imonumber}`
- **HTTP Method:** `GET`
- **Parameters:**
  | Name | Type | Required | Validation | Description |
  |------|------|----------|------------|-------------|
  | `imonumber` | `string` | Yes | Regex: `^[a-zA-Z0-9]+$`, Length: 1-10 | IMO number of the vessel |
  | `gdvno` | `string` | Yes | Regex: `^[a-zA-Z0-9]+$`, Length: 1-17 | GDV number (query param) |
  | `certificateno` | `string` | Yes | Regex: `^[a-zA-Z0-9]+$`, Length: 1-10 | Certificate number (query param) |
- **Response:** Array of certificates with vesselParticulars, certificateNumber, status, gdvNumber, grossTonnage, cargo, nextPortOfCall, nextPortOfCallCountry, dateAndTimeOfDeparture, dateAndTimeOfIssue, expiryDateAndTimeOfPortCertificate, nameOfMaster

---

#### Tool 12: `get_vessel_departure_declaration_by_imo`
- **Description:** Get vessel departure declaration by IMO number
- **Upstream URL:** `https://oceans-x.mpa.gov.sg/api/v1/vessel/departuredeclaration/1.0.0/imonumber/{imonumber}`
- **HTTP Method:** `GET`
- **Parameters:**
  | Name | Type | Required | Validation | Description |
  |------|------|----------|------------|-------------|
  | `imonumber` | `string` | Yes | Regex: `^[a-zA-Z0-9]+$`, Length: 1-10 | IMO number of the vessel |
- **Response:** Array of declarations with vesselParticulars, agent, nextPort, reportedArrivalTime, reportedDepartureTime, crew, pax

---

#### Tool 13: `get_vessel_departure_declarations_by_date`
- **Description:** Get vessel departure declarations by date
- **Upstream URL:** `https://oceans-x.mpa.gov.sg/api/v1/vessel/departuredeclaration/1.0.0/bydate`
- **HTTP Method:** `GET`
- **Parameters:**
  | Name | Type | Required | Validation | Description |
  |------|------|----------|------------|-------------|
  | `date` | `string` | Yes | Regex: `^\d{4}-\d{2}-\d{2}$` | Date in yyyy-MM-dd format (query param) |
- **Response:** Array of departure declarations

---

#### Tool 14: `get_vessel_departure_declarations_past_hours`
- **Description:** Get vessel departure declarations for past N hours
- **Upstream URL:** `https://oceans-x.mpa.gov.sg/api/v1/vessel/departuredeclaration/1.0.0/pastNhours`
- **HTTP Method:** `GET`
- **Parameters:**
  | Name | Type | Required | Validation | Description |
  |------|------|----------|------------|-------------|
  | `datetime` | `string` | Yes | Regex: `^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$` | Datetime (yyyy-MM-dd HH:mm:ss) (query param) |
  | `hours` | `string` | Yes | Regex: `^[\d]{1,2}(\.\d{1,2})?$` | Number of hours (query param) |
- **Response:** Array of departure declarations

---

### 2.4 Vessel Info Category

#### Tool 15: `get_vessel_particulars_by_name_pattern`
- **Description:** Get vessel particulars by vessel name pattern
- **Upstream URL:** `https://oceans-x.mpa.gov.sg/api/v1/vessel/particulars/1.0.0/name/{charset}`
- **HTTP Method:** `GET`
- **Parameters:**
  | Name | Type | Required | Validation | Description |
  |------|------|----------|------------|-------------|
  | `charset` | `string` | Yes | Regex: `^[0-9a-zA-Z-_. ']+$`, Length: 3-8 | Vessel name pattern to search |
- **Response:** Array of vessels with vesselName, imoNumber

---

#### Tool 16: `get_srs_certificate_by_certificate_number`
- **Description:** Get SRS (Singapore Registered Ships) certificate by certificate number
- **Upstream URL:** `https://oceans-x.mpa.gov.sg/api/v1/vessel/srscor/1.0.0/certificatenumber/{certificatenumber}`
- **HTTP Method:** `GET`
- **Parameters:**
  | Name | Type | Required | Validation | Description |
  |------|------|----------|------------|-------------|
  | `certificatenumber` | `string` | Yes | Regex: `^[0-9a-zA-Z-_. ']+$`, Length: 1-15 | SRS certificate number |
- **Response:** Array of certificates with shipName, imoNumber, registrationStatus, registrationDate, validityDate, dateOfClosure, certificateNumber, issueDate

---

#### Tool 17: `get_srs_certificate_by_vessel_details`
- **Description:** Get SRS certificate by vessel details
- **Upstream URL:** `https://oceans-x.mpa.gov.sg/api/v1/vessel/srscor/1.0.0/vesseldetails`
- **HTTP Method:** `GET`
- **Parameters:**
  | Name | Type | Required | Validation | Description |
  |------|------|----------|------------|-------------|
  | `officialnumber` | `string` | Yes | Regex: `^[a-zA-Z0-9]+$`, Length: 1-11 | Official number of the vessel |
  | `vesselname` | `string` | Yes | Regex: `^[0-9a-zA-Z-_. ']+$`, Length: 1-35 | Name of the vessel |
  | `registryportnumber` | `string` | Yes | Regex: `^[a-zA-Z0-9]+$`, Length: 1-8 | Registry port number |
  | `imonumber` | `string` | No | Regex: `^[a-zA-Z0-9]+$`, Length: 1-10 | IMO number (either this or callsign required) |
  | `callsign` | `string` | No | Regex: `^[a-zA-Z0-9]+$`, Length: 1-8 | Vessel call sign (either this or imonumber required) |
- **Response:** Array of SRS certificates

---

## 3. Shared Utilities

### 3.1 Validation Helpers (`validators.py`)

```python
# Pydantic validators for common patterns
DATE_PATTERN = r"^\d{4}-\d{2}-\d{2}$"
DATETIME_PATTERN = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"
HOURS_PATTERN = r"^[\d]{1,2}(\.\d{1,2})?$"
ALPHANUMERIC_PATTERN = r"^[a-zA-Z0-9]+$"
VESSEL_NAME_PATTERN = r"^[0-9a-zA-Z-_. ']+$"

# Validation functions
def validate_date(value: str) -> str
def validate_datetime(value: str) -> str
def validate_hours(value: str) -> str
def validate_alphanumeric(value: str, min_len: int, max_len: int) -> str
def validate_vessel_name(value: str, min_len: int, max_len: int) -> str
```

### 3.2 HTTP Client Wrapper (`http_client.py`)

```python
class MPAHttpClient:
    """Async HTTP client for MPA Oceans-X API calls"""
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
    
    async def get(
        self,
        url: str,
        apikey: str,
        params: dict | None = None
    ) -> dict:
        """
        Make GET request to upstream API
        - Forwards apikey header
        - Handles response codes (200, 204, 4xx, 5xx)
        - Returns parsed JSON or error dict
        """
```

### 3.3 Response Formatter (`response.py`)

```python
class MPAResponse:
    """Standardized response wrapper"""
    
    @staticmethod
    def success(data: list | dict) -> dict:
        return {"status": "success", "data": data}
    
    @staticmethod
    def no_content() -> dict:
        return {"status": "success", "data": [], "message": "No results found"}
    
    @staticmethod
    def error(code: int, message: str) -> dict:
        return {"status": "error", "code": code, "message": message}
```

### 3.4 Base URL Configuration (`config.py`)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Base URLs for each API category (configurable via env vars)
    MPA_ARRIVALS_BASE_URL: str = "https://oceans-x.mpa.gov.sg/api/v1/vessel/arrivals/1.0.0"
    MPA_DEPARTURES_BASE_URL: str = "https://oceans-x.mpa.gov.sg/api/v1/vessel/departure/1.0.0"
    MPA_DUE_TO_DEPART_BASE_URL: str = "https://oceans-x.mpa.gov.sg/api/v1/vessel/duetodepart/1.0.0"
    MPA_DUE_TO_ARRIVE_BASE_URL: str = "https://oceans-x.mpa.gov.sg/api/v1/vessel/duetoarrive/1.0.0"
    MPA_COUNTRIES_BASE_URL: str = "https://oceans-x.mpa.gov.sg/api/v1/mdhvessel/reference/countries/1.0.0"
    MPA_MOVEMENTS_BASE_URL: str = "https://oceans-x.mpa.gov.sg/api/v1/vessel/movements/1.0.0"
    MPA_POSITIONS_BASE_URL: str = "https://oceans-x.mpa.gov.sg/api/v1/vessel/positions/1.0.0"
    MPA_ARRIVAL_DECLARATION_BASE_URL: str = "https://oceans-x.mpa.gov.sg/api/v1/vessel/arrivaldeclaration/1.0.0"
    MPA_PORT_CLEARANCE_BASE_URL: str = "https://oceans-x.mpa.gov.sg/api/v1/vessel/portclearance/1.0.0"
    MPA_DEPARTURE_DECLARATION_BASE_URL: str = "https://oceans-x.mpa.gov.sg/api/v1/vessel/departuredeclaration/1.0.0"
    MPA_PARTICULARS_BASE_URL: str = "https://oceans-x.mpa.gov.sg/api/v1/vessel/particulars/1.0.0"
    MPA_SRSCOR_BASE_URL: str = "https://oceans-x.mpa.gov.sg/api/v1/vessel/srscor/1.0.0"
    
    # Server configuration
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 4. File Structure

```
mcp-server/
├── IMPLEMENTATION_PLAN.md     # This document
├── README.md                  # Usage documentation
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container image definition
├── .dockerignore              # Docker build exclusions
├── .env.example               # Example environment variables
├── server.py                  # Main FastMCP server entry point
└── src/
    ├── __init__.py
    ├── config.py              # Environment configuration
    ├── http_client.py         # Async HTTP client wrapper
    ├── response.py            # Response formatting utilities
    ├── validators.py          # Input validation helpers
    └── tools/
        ├── __init__.py
        ├── schedule.py        # Schedule category tools (5 tools)
        ├── port.py            # Port category tools (4 tools)
        ├── port_clearance.py  # Port Clearance category tools (5 tools)
        └── vessel_info.py     # Vessel Info category tools (3 tools)
```

### File Descriptions

| File | Purpose |
|------|---------|
| `server.py` | Main entry point. Initializes FastMCP server, registers all tools, configures HTTP transport on port 8000 |
| `src/config.py` | Pydantic settings for all environment variables and base URLs |
| `src/http_client.py` | Reusable async HTTP client that handles apikey forwarding and error responses |
| `src/response.py` | Consistent response wrapper for success/error cases |
| `src/validators.py` | Regex-based input validation functions |
| `src/tools/schedule.py` | 5 tools: arrivals, departures, due-to-depart, due-to-arrive (x2) |
| `src/tools/port.py` | 4 tools: country-codes, movements, positions-snapshot, positions-by-imo |
| `src/tools/port_clearance.py` | 5 tools: arrival-declaration, port-clearance-cert, departure-declaration (x3) |
| `src/tools/vessel_info.py` | 3 tools: particulars, srs-cert-by-number, srs-cert-by-details |

---

## 5. Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MPA_ARRIVALS_BASE_URL` | No | `https://oceans-x.mpa.gov.sg/api/v1/vessel/arrivals/1.0.0` | Vessel arrivals API base URL |
| `MPA_DEPARTURES_BASE_URL` | No | `https://oceans-x.mpa.gov.sg/api/v1/vessel/departure/1.0.0` | Vessel departures API base URL |
| `MPA_DUE_TO_DEPART_BASE_URL` | No | `https://oceans-x.mpa.gov.sg/api/v1/vessel/duetodepart/1.0.0` | Vessels due to depart API base URL |
| `MPA_DUE_TO_ARRIVE_BASE_URL` | No | `https://oceans-x.mpa.gov.sg/api/v1/vessel/duetoarrive/1.0.0` | Vessels due to arrive API base URL |
| `MPA_COUNTRIES_BASE_URL` | No | `https://oceans-x.mpa.gov.sg/api/v1/mdhvessel/reference/countries/1.0.0` | Country codes API base URL |
| `MPA_MOVEMENTS_BASE_URL` | No | `https://oceans-x.mpa.gov.sg/api/v1/vessel/movements/1.0.0` | Vessel movements API base URL |
| `MPA_POSITIONS_BASE_URL` | No | `https://oceans-x.mpa.gov.sg/api/v1/vessel/positions/1.0.0` | Vessel positions API base URL |
| `MPA_ARRIVAL_DECLARATION_BASE_URL` | No | `https://oceans-x.mpa.gov.sg/api/v1/vessel/arrivaldeclaration/1.0.0` | Arrival declarations API base URL |
| `MPA_PORT_CLEARANCE_BASE_URL` | No | `https://oceans-x.mpa.gov.sg/api/v1/vessel/portclearance/1.0.0` | Port clearance API base URL |
| `MPA_DEPARTURE_DECLARATION_BASE_URL` | No | `https://oceans-x.mpa.gov.sg/api/v1/vessel/departuredeclaration/1.0.0` | Departure declarations API base URL |
| `MPA_PARTICULARS_BASE_URL` | No | `https://oceans-x.mpa.gov.sg/api/v1/vessel/particulars/1.0.0` | Vessel particulars API base URL |
| `MPA_SRSCOR_BASE_URL` | No | `https://oceans-x.mpa.gov.sg/api/v1/vessel/srscor/1.0.0` | SRS certificate API base URL |
| `SERVER_HOST` | No | `0.0.0.0` | Server bind address |
| `SERVER_PORT` | No | `8000` | Server port |

---

## 6. Authentication Flow

The MPA Oceans-X APIs use API key authentication via the `apikey` HTTP header.

### Flow Diagram

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────────────┐
│  MCP Client │────▶│   MCP Server    │────▶│  MPA Oceans-X API    │
│             │     │   (FastMCP)     │     │                      │
└─────────────┘     └─────────────────┘     └──────────────────────┘
       │                    │                         │
       │  Tool call with    │                         │
       │  apikey parameter  │                         │
       │───────────────────▶│                         │
       │                    │                         │
       │                    │  HTTP GET with          │
       │                    │  apikey header          │
       │                    │────────────────────────▶│
       │                    │                         │
       │                    │      JSON response      │
       │                    │◀────────────────────────│
       │                    │                         │
       │   Structured       │                         │
       │   JSON result      │                         │
       │◀───────────────────│                         │
```

### Implementation Details

1. **MCP Client** includes `apikey` as a parameter in every tool call
2. **MCP Server** extracts `apikey` from tool parameters
3. **HTTP Client** adds `apikey` as a header: `headers={"apikey": apikey}`
4. **Upstream API** validates the key and returns data or 401/403 error

### Tool Parameter Schema

Every tool includes `apikey` as a required parameter:

```python
@mcp.tool()
async def get_vessel_arrivals_by_date(
    apikey: str,  # Required: MPA API key for authentication
    date: str,    # Required: Date in yyyy-MM-dd format
) -> dict:
    """Get vessel arrivals for a specific date."""
    ...
```

---

## 7. Deployment to Azure Container Apps

### Target Environment

| Setting | Value |
|---------|-------|
| Resource Group | `agentic-ai-demo-RG` |
| Container Apps Environment | `vnet-aca-env` |
| Container Port | `8000` |
| Image Registry | Azure Container Registry (to be created/specified) |

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run server
CMD ["python", "server.py"]
```

### requirements.txt

```
fastmcp>=0.1.0
httpx>=0.27.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
uvicorn>=0.30.0
```

### Deployment Steps

1. **Build and push container image:**
   ```bash
   az acr build --registry <acr-name> --image mpa-mcp-server:latest .
   ```

2. **Deploy to Container Apps:**
   ```bash
   az containerapp create \
     --name mpa-mcp-server \
     --resource-group agentic-ai-demo-RG \
     --environment vnet-aca-env \
     --image <acr-name>.azurecr.io/mpa-mcp-server:latest \
     --target-port 8000 \
     --ingress external \
     --min-replicas 1 \
     --max-replicas 3 \
     --cpu 0.5 \
     --memory 1Gi
   ```

3. **Configure environment variables (if overriding defaults):**
   ```bash
   az containerapp update \
     --name mpa-mcp-server \
     --resource-group agentic-ai-demo-RG \
     --set-env-vars "SERVER_PORT=8000"
   ```

### Health Check Endpoint

The server should expose a `/health` endpoint for Azure Container Apps health probes:

```python
@app.get("/health")
async def health():
    return {"status": "healthy"}
```

---

## 8. Implementation Notes

### 8.1 Error Handling Strategy

1. **Validation Errors (400):** Return structured error with field-level details
2. **Auth Errors (401/403):** Pass through upstream error message
3. **Not Found (404):** Return empty data array with message
4. **No Content (204):** Return success with empty data array
5. **Server Errors (5xx):** Return error with generic message, log details

### 8.2 URL Encoding

Parameters containing spaces (e.g., datetime `2025-08-30 18:58:46`) must be URL-encoded when constructing the upstream URL path.

### 8.3 Rate Limiting

The upstream API has rate limiting. The MCP server should:
- Pass through 400 errors about rate limits
- Consider adding retry logic with exponential backoff

### 8.4 Data Freshness

According to the swagger docs, data is updated at different intervals:
- Positions: every 3 minutes
- Movements: every 5 minutes
- Schedule data: every hour
- Particulars: every 6 hours

Include this information in tool descriptions.

### 8.5 Testing

Create tests for:
1. Input validation (regex patterns, length constraints)
2. HTTP client error handling
3. Response formatting
4. End-to-end tool calls with mocked upstream

---

## Summary

This implementation plan covers 17 MCP tools across 4 categories:

| Category | Tools | Upstream Base URL |
|----------|-------|-------------------|
| Schedule | 5 | Various `/vessel/*` endpoints |
| Port | 4 | `/mdhvessel/reference/*`, `/vessel/movements/*`, `/vessel/positions/*` |
| Port Clearance | 5 | `/vessel/arrivaldeclaration/*`, `/vessel/portclearance/*`, `/vessel/departuredeclaration/*` |
| Vessel Info | 3 | `/vessel/particulars/*`, `/vessel/srscor/*` |

**Total:** 17 MCP tools wrapping 17 MPA Oceans-X API endpoints.

---

*Generated: 2026-04-28*
