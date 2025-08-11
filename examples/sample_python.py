def calculate_user_score(user_id, scores):
    """Calculate the average score for a user
    
    Args:
        user_id (int): The ID of the user
        scores (list): List of numerical scores
    
    Returns:
        float: Average score
    """
    if not scores:
        return 0
    return sum(scores) / len(scores)

def get_user_profile(user_id):
    """Get user profile information
    
    Args:
        user_id (int): The ID of the user
    
    Returns:
        dict: User profile data
    """
    # This would typically fetch from a database
    return {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
        "created_at": "2024-01-01T00:00:00Z"
    }

async def send_notification(user_id, message, notification_type="email"):
    """Send a notification to a user
    
    Args:
        user_id (int): The ID of the user
        message (str): The notification message
        notification_type (str): Type of notification (email, sms, push)
    
    Returns:
        dict: Notification status
    """
    # Simulate async notification sending
    return {
        "status": "sent",
        "user_id": user_id,
        "type": notification_type,
        "message": message
    }

class UserManager:
    """Manages user-related operations"""
    
    def create_user(self, username, email, password):
        """Create a new user account
        
        Args:
            username (str): Desired username
            email (str): User's email address
            password (str): User's password
        
        Returns:
            dict: Created user information
        """
        # Hash password and save to database
        return {
            "message": "User created successfully",
            "username": username,
            "email": email
        }
    
    def authenticate_user(self, username, password):
        """Authenticate user credentials
        
        Args:
            username (str): Username
            password (str): Password
        
        Returns:
            dict: Authentication result with token
        """
        # Check credentials against database
        return {
            "authenticated": True,
            "token": "jwt_token_here",
            "expires_in": 3600
        }
    
    def delete_user(self, user_id, admin_password):
        """Delete a user account (admin only)
        
        Args:
            user_id (int): ID of user to delete
            admin_password (str): Admin password for verification
        
        Returns:
            dict: Deletion status
        """
        # This is a sensitive operation that should require admin auth
        return {"message": f"User {user_id} deleted successfully"}

def calculate_analytics(start_date, end_date, metrics=None):
    """Calculate analytics for a date range
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        metrics (list): List of metrics to calculate
    
    Returns:
        dict: Analytics data
    """
    if not metrics:
        metrics = ["users", "sessions", "revenue"]
    
    return {
        "period": f"{start_date} to {end_date}",
        "metrics": {metric: 100 for metric in metrics}
    }
