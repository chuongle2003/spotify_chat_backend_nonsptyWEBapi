# Admin Testing Guide

This guide explains how to test the admin functionality, create an admin account, and manage user permissions for the Spotify Chat API.

## Setting Up Environment Variables

1. Import the included Postman environment file (`POSTMAN_ENV.json`) to set up the testing environment
2. Import the included Postman collection file (`POSTMAN_COLLECTION.json`) to load all API endpoints

## Creating an Admin Account

You can create an admin account in two ways:

### Method 1: Using Django Command Line

```bash
python manage.py createsuperuser
```

Follow the prompts to enter email, username, and password.

### Method 2: Using existing admin to promote a user (requires an admin token)

1. Register a regular user first:

   ```
   POST {{base_url}}/api/accounts/auth/register/
   Body:
   {
     "email": "newadmin@example.com",
     "username": "newadmin",
     "password": "securePassword123",
     "first_name": "New",
     "last_name": "Admin"
   }
   ```

2. Login as an existing admin:

   ```
   POST {{base_url}}/api/auth/token/
   Body:
   {
     "email": "admin@example.com",
     "password": "adminPassword123"
   }
   ```

3. Make the user a staff member:

   ```
   POST {{base_url}}/api/user-management/{{user_id}}/toggle_staff/
   Headers: Authorization: Bearer {{admin_token}}
   Body: { "is_staff": true }
   ```

4. Make the user a superuser:
   ```
   POST {{base_url}}/api/user-management/{{user_id}}/toggle_superuser/
   Headers: Authorization: Bearer {{admin_token}}
   Body: { "is_superuser": true }
   ```

## Getting Admin Token

To use admin API endpoints, you need to obtain a token:

```
POST {{base_url}}/api/auth/token/
Body:
{
  "email": "admin@example.com",
  "password": "adminPassword123"
}
```

Save the received token in your Postman environment variable `token`.

## Testing Admin Permissions

### Viewing All Users (Admin Only)

```
GET {{base_url}}/api/user-management/users/
Headers: Authorization: Bearer {{token}}
```

### Creating Staff Users with Specific Permissions

1. Register a regular user
2. Make them a staff member (see above)
3. Assign specific permissions:
   ```
   POST {{base_url}}/api/user-management/{{staff_id}}/set_permissions/
   Headers: Authorization: Bearer {{admin_token}}
   Body:
   {
     "can_manage_users": true,
     "can_manage_content": false,
     "can_manage_playlists": true
   }
   ```

### Permission Test Matrix

Test the following scenarios with different user types:

| Action                 | Regular User | User Manager | Content Manager | Playlist Manager | Admin |
| ---------------------- | ------------ | ------------ | --------------- | ---------------- | ----- |
| View profile           | ✓            | ✓            | ✓               | ✓                | ✓     |
| Edit own profile       | ✓            | ✓            | ✓               | ✓                | ✓     |
| View all users         | ✗            | ✓            | ✗               | ✗                | ✓     |
| Edit other users       | ✗            | ✓            | ✗               | ✗                | ✓     |
| Upload songs           | ✗            | ✗            | ✓               | ✗                | ✓     |
| Edit songs             | ✗            | ✗            | ✓               | ✗                | ✓     |
| Create playlists       | ✓            | ✓            | ✓               | ✓                | ✓     |
| Feature playlists      | ✗            | ✗            | ✗               | ✓                | ✓     |
| Manage system settings | ✗            | ✗            | ✗               | ✗                | ✓     |

## Admin Account Fields

When viewing an admin account through the API, you'll see these fields:

- `id`: Unique identifier
- `username`: Admin username
- `email`: Admin email address
- `first_name`, `last_name`: Personal information
- `avatar`: Profile picture URL
- `bio`: Admin biography
- `is_active`: Account status
- `is_staff`: Staff status (true for admins)
- `is_superuser`: Superuser status (true for admins)
- `can_manage_users`, `can_manage_content`, `can_manage_playlists`: Permission flags
- `date_joined`: Account creation date
- `last_login`: Last authentication time
- `followers_count`, `following_count`: Social statistics

Note: Password information is never returned in API responses for security reasons.

## Test Automation

Use Postman collection runner to automate testing:

1. Set up environment variables
2. Configure the collection runner with the following test flow:
   - Create admin account
   - Get admin token
   - Register test users
   - Assign different permission levels
   - Test functionality for each user type
   - Verify expected access levels

## Troubleshooting

- If you receive a 403 Forbidden response, check the token and user permissions
- If admin creation fails, ensure the database is properly migrated:
  ```bash
  python manage.py migrate
  ```
- For token issues, verify the token hasn't expired and you're using the proper format in the Authorization header
