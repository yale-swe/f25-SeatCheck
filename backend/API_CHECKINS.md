# Check-In API Documentation

## Overview

The check-in feature allows users to report occupancy and noise levels at venues. This data is aggregated to provide real-time statistics.

## Base URL

- **Development:** `http://localhost:8000`
- **API Version:** `/api/v1`

## Authentication

Currently using mock authentication (user_id=1). Will be replaced with Yale CAS authentication.

---

## Endpoints

### 1. Create Check-In

**POST** `/api/v1/checkins`

Submit a new check-in for a venue.

#### Request Body

```json
{
  "venue_id": 1,
  "occupancy": 3,
  "noise": 2,
  "anonymous": true
}
```

#### Fields

- `venue_id` (integer, required): ID of the venue
- `occupancy` (integer, required): Occupancy level, 0-5 scale
  - 0 = Empty
  - 1 = Very Available
  - 2 = Available
  - 3 = Moderate
  - 4 = Busy
  - 5 = Packed
- `noise` (integer, required): Noise level, 0-5 scale
  - 0 = Silent
  - 1 = Very Quiet
  - 2 = Quiet
  - 3 = Moderate
  - 4 = Noisy
  - 5 = Very Loud
- `anonymous` (boolean, optional): Whether check-in is anonymous (default: true)

#### Response (201 Created)

```json
{
  "id": 123,
  "venue_id": 1,
  "user_id": 1,
  "occupancy": 3,
  "noise": 2,
  "anonymous": true,
  "created_at": "2025-10-28T12:34:56Z"
}
```

#### Error Responses

- **404 Not Found:** Venue doesn't exist
- **422 Unprocessable Entity:** Validation error (occupancy/noise out of range)

---

### 2. Get Venue Statistics

**GET** `/api/v1/venues/{venue_id}/stats`

Get aggregated statistics from recent check-ins.

#### Path Parameters

- `venue_id` (integer): ID of the venue

#### Query Parameters

- `minutes` (integer, optional): Time window in minutes (default: 2)

#### Example Request

```
GET /api/v1/venues/1/stats?minutes=2
```

#### Response (200 OK)

```json
{
  "venue_id": 1,
  "avg_occupancy": 3.2,
  "avg_noise": 2.1,
  "checkin_count": 5,
  "time_window_minutes": 2,
  "last_updated": "2025-10-28T12:34:56Z"
}
```

#### Response Fields

- `venue_id` (integer): Venue ID
- `avg_occupancy` (float | null): Average occupancy (0-5), null if no check-ins
- `avg_noise` (float | null): Average noise (0-5), null if no check-ins
- `checkin_count` (integer): Number of check-ins in time window
- `time_window_minutes` (integer): Time window used for aggregation
- `last_updated` (string): ISO 8601 timestamp when stats were calculated

#### Error Responses

- **404 Not Found:** Venue doesn't exist

---

## Frontend Integration Example

### TypeScript Types

```typescript
// Request
interface CheckInRequest {
  venue_id: number;
  occupancy: number; // 0-5
  noise: number; // 0-5
  anonymous?: boolean;
}

// Response
interface CheckInResponse {
  id: number;
  venue_id: number;
  user_id: number;
  occupancy: number;
  noise: number;
  anonymous: boolean;
  created_at: string; // ISO 8601
}

interface VenueStats {
  venue_id: number;
  avg_occupancy: number | null;
  avg_noise: number | null;
  checkin_count: number;
  time_window_minutes: number;
  last_updated: string; // ISO 8601
}
```

### Example API Client

```typescript
const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

export async function submitCheckin(data: CheckInRequest): Promise<CheckInResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/checkins`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  
  if (!response.ok) {
    throw new Error(`Check-in failed: ${response.statusText}`);
  }
  
  return response.json();
}

export async function getVenueStats(venueId: number, minutes: number = 2): Promise<VenueStats> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/venues/${venueId}/stats?minutes=${minutes}`
  );
  
  if (!response.ok) {
    throw new Error(`Failed to fetch stats: ${response.statusText}`);
  }
  
  return response.json();
}
```

---

## Testing

### Interactive API Docs

Start the backend server and visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Example cURL Commands

**Create Check-In:**
```bash
curl -X POST "http://localhost:8000/api/v1/checkins" \
  -H "Content-Type: application/json" \
  -d '{
    "venue_id": 1,
    "occupancy": 3,
    "noise": 2,
    "anonymous": true
  }'
```

**Get Stats:**
```bash
curl "http://localhost:8000/api/v1/venues/1/stats?minutes=2"
```

---

## Database Schema

### CheckIns Table

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary key |
| venue_id | integer | Foreign key to venues |
| user_id | integer | Foreign key to users |
| occupancy | integer | 0-5 scale |
| noise | integer | 0-5 scale |
| anonymous | boolean | Privacy flag |
| created_at | timestamp | Check-in time |

---

## Notes for Frontend

1. **Environment Variable:** Set `EXPO_PUBLIC_API_URL` in your `.env` file
2. **CORS:** Already configured to allow all origins in development
3. **Error Handling:** Check for 404 (venue not found) and 422 (validation errors)
4. **Time Window:** Stats use 2-minute window by default (configurable)
5. **Authentication:** Currently mocked - will be updated when CAS integration is ready

---

## Future Enhancements

- [ ] Real Yale CAS authentication
- [ ] Rate limiting per user
- [ ] WebSocket for real-time updates
- [ ] Historical data endpoints
- [ ] User check-in history

