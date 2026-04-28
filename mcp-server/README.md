# MPA Oceans-X MCP Server

A Python MCP (Model Context Protocol) server that wraps the Maritime and Port Authority (MPA) of Singapore Oceans-X APIs as MCP tools. Built with [FastMCP](https://github.com/jlowin/fastmcp) using streamable HTTP transport.

## Features

- 🚢 **17 MCP Tools** across 4 categories
- 🔐 **API Key Authentication** forwarded to upstream MPA APIs
- ✅ **Input Validation** with regex patterns and length constraints
- 🐳 **Docker Ready** for containerized deployment
- ☁️ **Azure Container Apps** deployment support

---

## Tools Reference

### Schedule Category (5 tools)

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `get_vessel_arrivals_by_date` | Get vessel arrivals for a specific date | `date` (yyyy-MM-dd) |
| `get_vessel_departures_past_hours` | Get departures for past N hours | `datetime`, `hours` |
| `get_vessels_due_to_depart_next_hours` | Get vessels due to depart | `datetime`, `hours` |
| `get_vessels_due_to_arrive_by_date` | Get vessels due to arrive by date | `date` (yyyy-MM-dd) |
| `get_vessels_due_to_arrive_next_hours` | Get vessels due to arrive next N hours | `datetime`, `hours` |

### Port Category (4 tools)

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `get_country_codes` | Get country codes reference data | None |
| `get_vessel_movements_by_callsign` | Get vessel movements | `callsign` (1-8 chars) |
| `get_vessel_positions_snapshot` | Get all vessel positions snapshot | None |
| `get_vessel_positions_by_imo` | Get vessel position by IMO | `imonumber` (1-10 chars) |

### Port Clearance Category (5 tools)

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `get_vessel_arrival_declaration_latest_by_name` | Get latest arrival declaration | `vesselname` (1-35 chars) |
| `get_port_clearance_certificate_by_imo` | Get port clearance certificate | `imonumber`, `gdvno`, `certificateno` |
| `get_vessel_departure_declaration_by_imo` | Get departure declaration | `imonumber` (1-10 chars) |
| `get_vessel_departure_declarations_by_date` | Get departure declarations by date | `date` (yyyy-MM-dd) |
| `get_vessel_departure_declarations_past_hours` | Get departure declarations past N hours | `datetime`, `hours` |

### Vessel Info Category (3 tools)

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `get_vessel_particulars_by_name_pattern` | Search vessels by name pattern | `charset` (3-8 chars) |
| `get_srs_certificate_by_certificate_number` | Get SRS certificate by number | `certificatenumber` (1-15 chars) |
| `get_srs_certificate_by_vessel_details` | Get SRS certificate by vessel details | `officialnumber`, `vesselname`, `registryportnumber`, +`imonumber` or `callsign` |

---

## Quick Start

### Prerequisites

- Python 3.11+
- MPA Oceans-X API key ([Register here](https://oceans-x.mpa.gov.sg))

### Run Locally

```bash
# Clone the repository
git clone https://github.com/janalee123/MPA-EBC.git
cd MPA-EBC/mcp-server

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python server.py
```

The server starts on `http://0.0.0.0:8000` by default.

### Run with Docker

```bash
# Build the image
docker build -t mpa-mcp-server .

# Run the container
docker run -p 8000:8000 mpa-mcp-server

# Or with custom port
docker run -p 9000:8000 -e SERVER_PORT=8000 mpa-mcp-server
```

---

## MCP Client Configuration

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mpa-oceans-x": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### Generic MCP Client

```python
from mcp import Client

async with Client("http://localhost:8000/mcp") as client:
    # List available tools
    tools = await client.list_tools()
    
    # Call a tool
    result = await client.call_tool(
        "get_vessel_arrivals_by_date",
        {
            "apikey": "your-mpa-api-key",
            "date": "2025-08-30"
        }
    )
    print(result)
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVER_HOST` | `0.0.0.0` | Server bind address |
| `SERVER_PORT` | `8000` | Server port |
| `MPA_ARRIVALS_BASE_URL` | `https://oceans-x.mpa.gov.sg/api/v1/vessel/arrivals/1.0.0` | Vessel arrivals API |
| `MPA_DEPARTURES_BASE_URL` | `https://oceans-x.mpa.gov.sg/api/v1/vessel/departure/1.0.0` | Vessel departures API |
| `MPA_DUE_TO_DEPART_BASE_URL` | `https://oceans-x.mpa.gov.sg/api/v1/vessel/duetodepart/1.0.0` | Due to depart API |
| `MPA_DUE_TO_ARRIVE_BASE_URL` | `https://oceans-x.mpa.gov.sg/api/v1/vessel/duetoarrive/1.0.0` | Due to arrive API |
| `MPA_COUNTRIES_BASE_URL` | `https://oceans-x.mpa.gov.sg/api/v1/mdhvessel/reference/countries/1.0.0` | Country codes API |
| `MPA_MOVEMENTS_BASE_URL` | `https://oceans-x.mpa.gov.sg/api/v1/vessel/movements/1.0.0` | Vessel movements API |
| `MPA_POSITIONS_BASE_URL` | `https://oceans-x.mpa.gov.sg/api/v1/vessel/positions/1.0.0` | Vessel positions API |
| `MPA_ARRIVAL_DECLARATION_BASE_URL` | `https://oceans-x.mpa.gov.sg/api/v1/vessel/arrivaldeclaration/1.0.0` | Arrival declarations API |
| `MPA_PORT_CLEARANCE_BASE_URL` | `https://oceans-x.mpa.gov.sg/api/v1/vessel/portclearance/1.0.0` | Port clearance API |
| `MPA_DEPARTURE_DECLARATION_BASE_URL` | `https://oceans-x.mpa.gov.sg/api/v1/vessel/departuredeclaration/1.0.0` | Departure declarations API |
| `MPA_PARTICULARS_BASE_URL` | `https://oceans-x.mpa.gov.sg/api/v1/vessel/particulars/1.0.0` | Vessel particulars API |
| `MPA_SRSCOR_BASE_URL` | `https://oceans-x.mpa.gov.sg/api/v1/vessel/srscor/1.0.0` | SRS certificate API |

---

## API Authentication

All tools require an `apikey` parameter. This API key is obtained from the MPA Oceans-X developer portal and is forwarded as an HTTP header to the upstream MPA APIs.

```
MCP Client → MCP Server → MPA Oceans-X API
   │              │              │
   │  apikey      │  apikey      │
   │  parameter   │  header      │
   └──────────────┴──────────────┘
```

---

## Response Format

All tools return a consistent response structure:

### Success
```json
{
  "status": "success",
  "data": [...]
}
```

### No Results
```json
{
  "status": "success",
  "data": [],
  "message": "No results found"
}
```

### Error
```json
{
  "status": "error",
  "code": 401,
  "message": "Invalid API key"
}
```

---

## Deployment

### Azure Container Apps

```bash
# Build and push to Azure Container Registry
az acr build --registry <acr-name> --image mpa-mcp-server:latest .

# Deploy to Container Apps
az containerapp create \
  --name mpa-mcp-server \
  --resource-group agentic-ai-demo-RG \
  --environment vnet-aca-env \
  --image <acr-name>.azurecr.io/mpa-mcp-server:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3
```

---

## Data Freshness

The MPA Oceans-X APIs update at different intervals:

| Data Type | Update Frequency |
|-----------|------------------|
| Vessel Positions | Every 3 minutes |
| Vessel Movements | Every 5 minutes |
| Schedule Data | Every hour |
| Vessel Particulars | Every 6 hours |

---

## License

MIT

---

## Links

- [MPA Oceans-X API Portal](https://oceans-x.mpa.gov.sg)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Model Context Protocol](https://modelcontextprotocol.io)
