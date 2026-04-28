"""
MPA Oceans-X MCP Server

A FastMCP server that wraps the Maritime and Port Authority (MPA) of Singapore
Oceans-X APIs as MCP tools. Provides access to vessel schedules, positions,
port clearance, and vessel information.

Usage:
    python server.py

Environment Variables:
    SERVER_HOST: Server bind address (default: 0.0.0.0)
    SERVER_PORT: Server port (default: 8000)
    MPA_*_BASE_URL: Override default base URLs for each API category
"""

import os
import re
from typing import Any
from urllib.parse import quote

import httpx
from fastmcp import FastMCP

# =============================================================================
# Configuration
# =============================================================================

SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

# Base URLs for MPA Oceans-X APIs
BASE_URLS = {
    "arrivals": os.getenv(
        "MPA_ARRIVALS_BASE_URL",
        "https://oceans-x.mpa.gov.sg/api/v1/vessel/arrivals/1.0.0"
    ),
    "departures": os.getenv(
        "MPA_DEPARTURES_BASE_URL",
        "https://oceans-x.mpa.gov.sg/api/v1/vessel/departure/1.0.0"
    ),
    "due_to_depart": os.getenv(
        "MPA_DUE_TO_DEPART_BASE_URL",
        "https://oceans-x.mpa.gov.sg/api/v1/vessel/duetodepart/1.0.0"
    ),
    "due_to_arrive": os.getenv(
        "MPA_DUE_TO_ARRIVE_BASE_URL",
        "https://oceans-x.mpa.gov.sg/api/v1/vessel/duetoarrive/1.0.0"
    ),
    "countries": os.getenv(
        "MPA_COUNTRIES_BASE_URL",
        "https://oceans-x.mpa.gov.sg/api/v1/mdhvessel/reference/countries/1.0.0"
    ),
    "movements": os.getenv(
        "MPA_MOVEMENTS_BASE_URL",
        "https://oceans-x.mpa.gov.sg/api/v1/vessel/movements/1.0.0"
    ),
    "positions": os.getenv(
        "MPA_POSITIONS_BASE_URL",
        "https://oceans-x.mpa.gov.sg/api/v1/vessel/positions/1.0.0"
    ),
    "arrival_declaration": os.getenv(
        "MPA_ARRIVAL_DECLARATION_BASE_URL",
        "https://oceans-x.mpa.gov.sg/api/v1/vessel/arrivaldeclaration/1.0.0"
    ),
    "port_clearance": os.getenv(
        "MPA_PORT_CLEARANCE_BASE_URL",
        "https://oceans-x.mpa.gov.sg/api/v1/vessel/portclearance/1.0.0"
    ),
    "departure_declaration": os.getenv(
        "MPA_DEPARTURE_DECLARATION_BASE_URL",
        "https://oceans-x.mpa.gov.sg/api/v1/vessel/departuredeclaration/1.0.0"
    ),
    "particulars": os.getenv(
        "MPA_PARTICULARS_BASE_URL",
        "https://oceans-x.mpa.gov.sg/api/v1/vessel/particulars/1.0.0"
    ),
    "srscor": os.getenv(
        "MPA_SRSCOR_BASE_URL",
        "https://oceans-x.mpa.gov.sg/api/v1/vessel/srscor/1.0.0"
    ),
}

# =============================================================================
# Validation Patterns
# =============================================================================

PATTERNS = {
    "date": re.compile(r"^\d{4}-\d{2}-\d{2}$"),
    "datetime": re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"),
    "hours": re.compile(r"^[\d]{1,2}(\.\d{1,2})?$"),
    "alphanumeric": re.compile(r"^[a-zA-Z0-9]+$"),
    "vessel_name": re.compile(r"^[0-9a-zA-Z\-_. ']+$"),
}


# =============================================================================
# Validation Functions
# =============================================================================

def validate_date(value: str) -> str:
    """Validate date format (yyyy-MM-dd)."""
    if not PATTERNS["date"].match(value):
        raise ValueError(f"Invalid date format: {value}. Expected yyyy-MM-dd")
    return value


def validate_datetime(value: str) -> str:
    """Validate datetime format (yyyy-MM-dd HH:mm:ss)."""
    if not PATTERNS["datetime"].match(value):
        raise ValueError(f"Invalid datetime format: {value}. Expected yyyy-MM-dd HH:mm:ss")
    return value


def validate_hours(value: str) -> str:
    """Validate hours format (1-2 digits, optional decimal)."""
    if not PATTERNS["hours"].match(value):
        raise ValueError(f"Invalid hours format: {value}. Expected 1-99 with optional decimal")
    return value


def validate_alphanumeric(value: str, min_len: int, max_len: int, field_name: str) -> str:
    """Validate alphanumeric string with length constraints."""
    if not PATTERNS["alphanumeric"].match(value):
        raise ValueError(f"Invalid {field_name}: must be alphanumeric")
    if not (min_len <= len(value) <= max_len):
        raise ValueError(f"Invalid {field_name}: length must be {min_len}-{max_len} characters")
    return value


def validate_vessel_name(value: str, min_len: int, max_len: int) -> str:
    """Validate vessel name with allowed characters and length."""
    if not PATTERNS["vessel_name"].match(value):
        raise ValueError(f"Invalid vessel name: contains invalid characters")
    if not (min_len <= len(value) <= max_len):
        raise ValueError(f"Invalid vessel name: length must be {min_len}-{max_len} characters")
    return value


# =============================================================================
# HTTP Client
# =============================================================================

async def mpa_request(
    url: str,
    apikey: str,
    params: dict[str, str] | None = None,
    timeout: float = 30.0
) -> dict[str, Any]:
    """
    Make an HTTP GET request to MPA Oceans-X API.
    
    Args:
        url: Full URL to request
        apikey: MPA API key for authentication
        params: Optional query parameters
        timeout: Request timeout in seconds
    
    Returns:
        Dict with status, data, and optional message/error fields
    """
    headers = {"apikey": apikey}
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                return {"status": "success", "data": response.json()}
            elif response.status_code == 204:
                return {"status": "success", "data": [], "message": "No results found"}
            elif response.status_code == 401:
                return {"status": "error", "code": 401, "message": "Invalid API key"}
            elif response.status_code == 403:
                return {"status": "error", "code": 403, "message": "Access denied"}
            elif response.status_code == 404:
                return {"status": "error", "code": 404, "message": "Resource not found"}
            elif response.status_code == 400:
                return {"status": "error", "code": 400, "message": "Bad request - check parameters or rate limit exceeded"}
            else:
                return {"status": "error", "code": response.status_code, "message": f"Upstream error: {response.text[:200]}"}
        
        except httpx.TimeoutException:
            return {"status": "error", "code": 504, "message": "Request timed out"}
        except httpx.RequestError as e:
            return {"status": "error", "code": 502, "message": f"Request failed: {str(e)}"}


# =============================================================================
# FastMCP Server Initialization
# =============================================================================

mcp = FastMCP(
    name="mpa-oceans-x",
    instructions="""
    MPA Oceans-X MCP Server - Access Singapore Maritime and Port Authority vessel data.
    
    This server provides 17 tools across 4 categories:
    - Schedule: Vessel arrivals, departures, and expected movements
    - Port: Country codes, vessel movements, and positions
    - Port Clearance: Arrival/departure declarations and clearance certificates
    - Vessel Info: Vessel particulars and Singapore registered ship certificates
    
    All tools require an 'apikey' parameter for MPA API authentication.
    """
)


# =============================================================================
# Schedule Category Tools (5 tools)
# =============================================================================

@mcp.tool()
async def get_vessel_arrivals_by_date(apikey: str, date: str) -> dict[str, Any]:
    """
    Get vessel arrivals for a specific date.
    
    Data is updated every hour.
    
    Args:
        apikey: MPA Oceans-X API key for authentication
        date: Date in yyyy-MM-dd format (e.g., "2025-08-30")
    
    Returns:
        List of vessel arrivals with vesselParticulars, arrivedTime, locationFrom, locationTo
    """
    validate_date(date)
    url = f"{BASE_URLS['arrivals']}/date/{date}"
    return await mpa_request(url, apikey)


@mcp.tool()
async def get_vessel_departures_past_hours(apikey: str, datetime: str, hours: str) -> dict[str, Any]:
    """
    Get vessel departures for the past N hours from a given datetime.
    
    Data is updated every hour.
    
    Args:
        apikey: MPA Oceans-X API key for authentication
        datetime: Start datetime in yyyy-MM-dd HH:mm:ss format (e.g., "2025-08-30 18:58:46")
        hours: Number of hours to look back (1-99, optional decimal e.g., "3" or "3.5")
    
    Returns:
        List of vessel departures with vesselParticulars and departedTime
    """
    validate_datetime(datetime)
    validate_hours(hours)
    encoded_datetime = quote(datetime, safe='')
    url = f"{BASE_URLS['departures']}/date/{encoded_datetime}/hours/{hours}"
    return await mpa_request(url, apikey)


@mcp.tool()
async def get_vessels_due_to_depart_next_hours(apikey: str, datetime: str, hours: str) -> dict[str, Any]:
    """
    Get vessels due to depart for the next N hours from a given datetime.
    
    Data is updated every hour.
    
    Args:
        apikey: MPA Oceans-X API key for authentication
        datetime: Start datetime in yyyy-MM-dd HH:mm:ss format (e.g., "2025-08-30 08:00:00")
        hours: Number of hours to look ahead (1-99, optional decimal e.g., "10" or "10.5")
    
    Returns:
        List of vessels with vesselParticulars and dueToDepart time
    """
    validate_datetime(datetime)
    validate_hours(hours)
    encoded_datetime = quote(datetime, safe='')
    url = f"{BASE_URLS['due_to_depart']}/date/{encoded_datetime}/hours/{hours}"
    return await mpa_request(url, apikey)


@mcp.tool()
async def get_vessels_due_to_arrive_by_date(apikey: str, date: str) -> dict[str, Any]:
    """
    Get vessels due to arrive for a specific date.
    
    Data is updated every hour.
    
    Args:
        apikey: MPA Oceans-X API key for authentication
        date: Date in yyyy-MM-dd format (e.g., "2025-08-30")
    
    Returns:
        List of vessels with vesselParticulars, duetoArriveTime, locationFrom, locationTo
    """
    validate_date(date)
    url = f"{BASE_URLS['due_to_arrive']}/date/{date}"
    return await mpa_request(url, apikey)


@mcp.tool()
async def get_vessels_due_to_arrive_next_hours(apikey: str, datetime: str, hours: str) -> dict[str, Any]:
    """
    Get vessels due to arrive for the next N hours from a given datetime.
    
    Data is updated every hour.
    
    Args:
        apikey: MPA Oceans-X API key for authentication
        datetime: Start datetime in yyyy-MM-dd HH:mm:ss format (e.g., "2025-08-30 00:20:31")
        hours: Number of hours to look ahead (1-99, optional decimal e.g., "10")
    
    Returns:
        List of vessels with vesselParticulars, duetoArriveTime, locationFrom, locationTo
    """
    validate_datetime(datetime)
    validate_hours(hours)
    encoded_datetime = quote(datetime, safe='')
    url = f"{BASE_URLS['due_to_arrive']}/date/{encoded_datetime}/hours/{hours}"
    return await mpa_request(url, apikey)


# =============================================================================
# Port Category Tools (4 tools)
# =============================================================================

@mcp.tool()
async def get_country_codes(apikey: str) -> dict[str, Any]:
    """
    Get country codes reference data in JSON format.
    
    Returns a list of country codes with nationality, country description, and timestamp.
    
    Args:
        apikey: MPA Oceans-X API key for authentication
    
    Returns:
        List of country codes with nationality, timeStamp, countryCode, countryDescription
    """
    url = f"{BASE_URLS['countries']}/filetype/json"
    return await mpa_request(url, apikey)


@mcp.tool()
async def get_vessel_movements_by_callsign(apikey: str, callsign: str) -> dict[str, Any]:
    """
    Get vessel movements by call sign.
    
    Data is updated every 5 minutes.
    
    Args:
        apikey: MPA Oceans-X API key for authentication
        callsign: Vessel call sign (1-8 alphanumeric characters, e.g., "D7AZ")
    
    Returns:
        List of movements with vesselParticulars, movementStartDateTime, movementEndDateTime,
        movementStatus, movementType, locationFrom, locationTo, movementDraft, movementHeight
    """
    validate_alphanumeric(callsign, 1, 8, "callsign")
    url = f"{BASE_URLS['movements']}/callsign/{callsign}"
    return await mpa_request(url, apikey)


@mcp.tool()
async def get_vessel_positions_snapshot(apikey: str) -> dict[str, Any]:
    """
    Get a snapshot of all vessel positions in Singapore port waters.
    
    Data is updated every 3 minutes. Returns comprehensive vessel information
    including position, speed, course, and vessel particulars.
    
    Args:
        apikey: MPA Oceans-X API key for authentication
    
    Returns:
        List of vessel positions with vesselParticulars (including extended fields like
        vesselLength, grossTonnage, mmsiNumber), latitude, longitude, speed, course,
        heading, dimA, dimB, timeStamp
    """
    url = f"{BASE_URLS['positions']}/snapshot"
    return await mpa_request(url, apikey)


@mcp.tool()
async def get_vessel_positions_by_imo(apikey: str, imonumber: str) -> dict[str, Any]:
    """
    Get vessel position by IMO number.
    
    Data is updated every 3 minutes.
    
    Args:
        apikey: MPA Oceans-X API key for authentication
        imonumber: IMO number of the vessel (1-10 alphanumeric characters, e.g., "9214898")
    
    Returns:
        List of vessel positions with full vesselParticulars, coordinates, speed, course, heading
    """
    validate_alphanumeric(imonumber, 1, 10, "imonumber")
    url = f"{BASE_URLS['positions']}/imonumber/{imonumber}"
    return await mpa_request(url, apikey)


# =============================================================================
# Port Clearance Category Tools (5 tools)
# =============================================================================

@mcp.tool()
async def get_vessel_arrival_declaration_latest_by_name(apikey: str, vesselname: str) -> dict[str, Any]:
    """
    Get the latest vessel arrival declaration by vessel name.
    
    Data is updated every hour.
    
    Args:
        apikey: MPA Oceans-X API key for authentication
        vesselname: Name of the vessel (1-35 characters, e.g., "RADJA SAMUDERA ABADI")
    
    Returns:
        List of declarations with vesselParticulars, location, grid, purpose, agent,
        reportedArrivalTime, crew, pax. The purpose field is CSV with Y/N indicators for:
        Loading/Unloading Cargo, Passengers, Taking Bunker, Ship Supplies, Changing Crew,
        Shipyard Repair, Offshore Support, Not Used, Other Afloat Activities
    """
    validate_vessel_name(vesselname, 1, 35)
    encoded_name = quote(vesselname, safe='')
    url = f"{BASE_URLS['arrival_declaration']}/last/vesselname/{encoded_name}"
    return await mpa_request(url, apikey)


@mcp.tool()
async def get_port_clearance_certificate_by_imo(
    apikey: str,
    imonumber: str,
    gdvno: str,
    certificateno: str
) -> dict[str, Any]:
    """
    Get port clearance certificate by IMO number, GDV number, and certificate number.
    
    Data is updated every hour.
    
    Args:
        apikey: MPA Oceans-X API key for authentication
        imonumber: IMO number of the vessel (1-10 alphanumeric characters, e.g., "9762156")
        gdvno: GDV number of the vessel (1-17 alphanumeric characters, e.g., "850524")
        certificateno: Certificate number (1-10 alphanumeric characters, e.g., "E84204")
    
    Returns:
        List of certificates with vesselParticulars, certificateNumber, status, gdvNumber,
        grossTonnage, cargo, nextPortOfCall, nextPortOfCallCountry, dateAndTimeOfDeparture,
        dateAndTimeOfIssue, expiryDateAndTimeOfPortCertificate, nameOfMaster
    """
    validate_alphanumeric(imonumber, 1, 10, "imonumber")
    validate_alphanumeric(gdvno, 1, 17, "gdvno")
    validate_alphanumeric(certificateno, 1, 10, "certificateno")
    url = f"{BASE_URLS['port_clearance']}/imonumber/{imonumber}"
    params = {"gdvno": gdvno, "certificateno": certificateno}
    return await mpa_request(url, apikey, params=params)


@mcp.tool()
async def get_vessel_departure_declaration_by_imo(apikey: str, imonumber: str) -> dict[str, Any]:
    """
    Get vessel departure declaration by IMO number.
    
    Data is updated every hour.
    
    Args:
        apikey: MPA Oceans-X API key for authentication
        imonumber: IMO number of the vessel (1-10 alphanumeric characters, e.g., "1103512")
    
    Returns:
        List of declarations with vesselParticulars, agent, nextPort, reportedArrivalTime,
        reportedDepartureTime, crew, pax
    """
    validate_alphanumeric(imonumber, 1, 10, "imonumber")
    url = f"{BASE_URLS['departure_declaration']}/imonumber/{imonumber}"
    return await mpa_request(url, apikey)


@mcp.tool()
async def get_vessel_departure_declarations_by_date(apikey: str, date: str) -> dict[str, Any]:
    """
    Get all vessel departure declarations for a specific date.
    
    Data is updated every hour.
    
    Args:
        apikey: MPA Oceans-X API key for authentication
        date: Date in yyyy-MM-dd format (e.g., "2025-07-26")
    
    Returns:
        List of departure declarations with vesselParticulars, agent, nextPort,
        reportedArrivalTime, reportedDepartureTime, crew, pax
    """
    validate_date(date)
    url = f"{BASE_URLS['departure_declaration']}/bydate"
    params = {"date": date}
    return await mpa_request(url, apikey, params=params)


@mcp.tool()
async def get_vessel_departure_declarations_past_hours(
    apikey: str,
    datetime: str,
    hours: str
) -> dict[str, Any]:
    """
    Get vessel departure declarations for the past N hours from a given datetime.
    
    Data is updated every hour.
    
    Args:
        apikey: MPA Oceans-X API key for authentication
        datetime: Datetime in yyyy-MM-dd HH:mm:ss format (e.g., "2025-07-27 00:00:00")
        hours: Number of hours to look back (1-99, optional decimal e.g., "24")
    
    Returns:
        List of departure declarations with vesselParticulars, agent, nextPort,
        reportedArrivalTime, reportedDepartureTime, crew, pax
    """
    validate_datetime(datetime)
    validate_hours(hours)
    url = f"{BASE_URLS['departure_declaration']}/pastNhours"
    params = {"datetime": datetime, "hours": hours}
    return await mpa_request(url, apikey, params=params)


# =============================================================================
# Vessel Info Category Tools (3 tools)
# =============================================================================

@mcp.tool()
async def get_vessel_particulars_by_name_pattern(apikey: str, charset: str) -> dict[str, Any]:
    """
    Get vessel particulars by vessel name pattern.
    
    Searches for vessels whose names match the provided character pattern.
    Data is updated every 6 hours.
    
    Args:
        apikey: MPA Oceans-X API key for authentication
        charset: Vessel name pattern to search (3-8 characters, e.g., "BINTANG")
    
    Returns:
        List of vessels with vesselName and imoNumber
    """
    validate_vessel_name(charset, 3, 8)
    encoded_charset = quote(charset, safe='')
    url = f"{BASE_URLS['particulars']}/name/{encoded_charset}"
    return await mpa_request(url, apikey)


@mcp.tool()
async def get_srs_certificate_by_certificate_number(apikey: str, certificatenumber: str) -> dict[str, Any]:
    """
    Get Singapore Registered Ships (SRS) certificate by certificate number.
    
    Data is updated every hour.
    
    Args:
        apikey: MPA Oceans-X API key for authentication
        certificatenumber: SRS certificate number (1-15 characters, e.g., "COR-0001-18")
    
    Returns:
        List of certificates with shipName, imoNumber, registrationStatus, registrationDate,
        validityDate, dateOfClosure, certificateNumber, issueDate
    """
    validate_vessel_name(certificatenumber, 1, 15)  # Same pattern as vessel_name
    encoded_cert = quote(certificatenumber, safe='')
    url = f"{BASE_URLS['srscor']}/certificatenumber/{encoded_cert}"
    return await mpa_request(url, apikey)


@mcp.tool()
async def get_srs_certificate_by_vessel_details(
    apikey: str,
    officialnumber: str,
    vesselname: str,
    registryportnumber: str,
    imonumber: str | None = None,
    callsign: str | None = None
) -> dict[str, Any]:
    """
    Get Singapore Registered Ships (SRS) certificate by vessel details.
    
    Either imonumber or callsign must be provided.
    Data is updated every hour.
    
    Args:
        apikey: MPA Oceans-X API key for authentication
        officialnumber: Official number of the vessel (1-11 alphanumeric, e.g., "401405")
        vesselname: Name of the vessel (1-35 characters, e.g., "OCEAN DROVER")
        registryportnumber: Registry port number (1-8 alphanumeric, e.g., "01410E18")
        imonumber: IMO number (1-10 alphanumeric, e.g., "9232852") - optional if callsign provided
        callsign: Vessel call sign (1-8 alphanumeric, e.g., "9V9362") - optional if imonumber provided
    
    Returns:
        List of SRS certificates with shipName, imoNumber, registrationStatus,
        registrationDate, validityDate, dateOfClosure, certificateNumber, issueDate
    """
    validate_alphanumeric(officialnumber, 1, 11, "officialnumber")
    validate_vessel_name(vesselname, 1, 35)
    validate_alphanumeric(registryportnumber, 1, 8, "registryportnumber")
    
    if not imonumber and not callsign:
        raise ValueError("Either imonumber or callsign must be provided")
    
    if imonumber:
        validate_alphanumeric(imonumber, 1, 10, "imonumber")
    if callsign:
        validate_alphanumeric(callsign, 1, 8, "callsign")
    
    url = f"{BASE_URLS['srscor']}/vesseldetails"
    params = {
        "officialnumber": officialnumber,
        "vesselname": vesselname,
        "registryportnumber": registryportnumber,
    }
    if imonumber:
        params["imonumber"] = imonumber
    if callsign:
        params["callsign"] = callsign
    
    return await mpa_request(url, apikey, params=params)


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print(f"Starting MPA Oceans-X MCP Server on {SERVER_HOST}:{SERVER_PORT}")
    print(f"Tools registered: 17")
    print(f"Categories: Schedule (5), Port (4), Port Clearance (5), Vessel Info (3)")
    
    # Run with streamable HTTP transport
    uvicorn.run(
        mcp.http_app(),
        host=SERVER_HOST,
        port=SERVER_PORT,
        log_level="info"
    )
