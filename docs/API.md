# GitRev — API Documentation

Base URL: `http://localhost:5000`

---

## Health

### `GET /health`
Check that the server is running.

**Response**
```json
{ "status": "ok" }
```

---

## Users

### `GET /users/v1/api/users`
Returns a list of all users.

**Response**
```json
[
  { "id": 1, "name": "Jane Doe", "email": "jane@example.com" }
]
```

### `GET /users/v1/api/users/<id>`
Returns a single user by ID.

**Response**
```json
{ "id": 1, "name": "Jane Doe", "email": "jane@example.com" }
```

### `POST /users/v1/api/users`
Creates a new user.

**Request Body**
```json
{ "name": "Jane Doe", "email": "jane@example.com" }
```

**Response**
```json
{ "id": 2, "name": "Jane Doe", "email": "jane@example.com" }
```

### `DELETE /users/v1/api/users/<id>`
Deletes a user by ID.

**Response**
```json
{ "deleted": true }
```

---

## URLs

### `GET /urls/v1/api/urls`
Returns a list of all URLs.

**Response**
```json
[
  { "id": 1, "url": "https://example.com", "label": "Example" }
]
```

### `GET /urls/v1/api/urls/<id>`
Returns a single URL by ID.

**Response**
```json
{ "id": 1, "url": "https://example.com", "label": "Example" }
```

### `POST /urls/v1/api/urls`
Creates a new URL entry.

**Request Body**
```json
{ "url": "https://example.com", "label": "Example" }
```

**Response**
```json
{ "id": 2, "url": "https://example.com", "label": "Example" }
```

### `DELETE /urls/v1/api/urls/<id>`
Deletes a URL by ID.

**Response**
```json
{ "deleted": true }
```

---

## Events

### `GET /events/v1/api/events`
Returns a list of all events.

**Response**
```json
[
  { "id": 1, "name": "Deploy", "timestamp": "2026-04-04T10:00:00Z" }
]
```

### `GET /events/v1/api/events/<id>`
Returns a single event by ID.

**Response**
```json
{ "id": 1, "name": "Deploy", "timestamp": "2026-04-04T10:00:00Z" }
```

### `POST /events/v1/api/events`
Creates a new event.

**Request Body**
```json
{ "name": "Deploy", "timestamp": "2026-04-04T10:00:00Z" }
```

**Response**
```json
{ "id": 2, "name": "Deploy", "timestamp": "2026-04-04T10:00:00Z" }
```

### `DELETE /events/v1/api/events/<id>`
Deletes an event by ID.

**Response**
```json
{ "deleted": true }
```

---

## Error Responses

| Status | Meaning |
|---|---|
| `400` | Bad request — invalid input |
| `404` | Resource not found |
| `500` | Internal server error |
