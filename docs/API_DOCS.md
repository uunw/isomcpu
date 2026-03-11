# ISOMCOM API Documentation

## 🔐 Authentication
All technician APIs require a Bearer Token.

## 🛡️ Technician Endpoints (`/api/tech`)

### 1. Login
- **Endpoint:** `/api/tech/login`
- **Method:** `POST`
- **Description:** Technician authentication (OAuth2 Password flow).
- **Body:** `username` (email), `password`

### 2. Update Repair Status
- **Endpoint:** `/api/tech/repair/update`
- **Method:** `PUT`
- **Description:** Update status of a repair request. Enforces strict sequential order.
- **Params:** `queue_id`, `status_name`

### 3. List Repairs
- **Endpoint:** `/api/tech/repairs`
- **Method:** `GET`
- **Description:** Technician retrieves assigned repair requests.

## 🛠️ Repair Endpoints (`/api/repairs`)

### 1. Create Repair Request
- **Endpoint:** `/api/repairs/create`
- **Method:** `POST`

### 2. Track Repair
- **Endpoint:** `/api/repairs/track`
- **Method:** `GET`
- **Params:** `line_user_id`

### 3. All Repairs (Admin View)
- **Endpoint:** `/api/repairs/all`
- **Method:** `GET`
