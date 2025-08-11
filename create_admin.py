#!/usr/bin/env python3
"""
Minimal script to create admin user from environment variables
Usage: python create_admin.py
Environment variables:
- ADMIN_EMAIL: Admin email address
- ADMIN_NAME: Admin display name  
- ADMIN_PASSWORD: Admin password
- DB_HOST: Database host
- DB_PORT: Database port
- DB_NAME: Database name
- DB_USER: Database username
- DB_PASSWORD: Database password
"""

import os
import sys
import psycopg2
import bcrypt
from typing import Optional

def get_env_var(name: str, required: bool = True) -> Optional[str]:
    """Get environment variable value"""
    value = os.getenv(name)
    if required and not value:
        print(f"ERROR: Required environment variable {name} is not set")
        sys.exit(1)
    return value

def create_admin_user():
    """Create admin user from environment variables"""
    
    # Get database connection details
    db_host = get_env_var('DB_HOST')
    db_port = get_env_var('DB_PORT', required=False) or '5432'
    db_name = get_env_var('DB_NAME')
    db_user = get_env_var('DB_USER')
    db_password = get_env_var('DB_PASSWORD')
    
    # Get admin details
    admin_email = get_env_var('ADMIN_EMAIL')
    admin_name = get_env_var('ADMIN_NAME')
    admin_password = get_env_var('ADMIN_PASSWORD')
    
    # Hash password
    password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        
        with conn.cursor() as cur:
            # Check if user exists
            cur.execute("SELECT 1 FROM auth.users WHERE email = %s", (admin_email,))
            user_exists = cur.fetchone()
            
            if user_exists:
                # Update existing user
                cur.execute("""
                    UPDATE auth.users 
                    SET role = 'admin', name = %s, password_hash = %s
                    WHERE email = %s
                """, (admin_name, password_hash, admin_email))
                print(f"Updated existing user {admin_email} to admin")
            else:
                # Create new admin user
                cur.execute("""
                    INSERT INTO auth.users (email, name, password_hash, role) 
                    VALUES (%s, %s, %s, 'admin')
                """, (admin_email, admin_name, password_hash))
                print(f"Created new admin user {admin_email}")
            
            conn.commit()
            print(f"Admin user '{admin_name}' ({admin_email}) ready")
            
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    create_admin_user()
