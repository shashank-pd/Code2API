/**
 * Sample Java file for Code2API demonstration
 */
import java.util.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class UserManager {
    
    private Map<Integer, User> users;
    
    public UserManager() {
        this.users = new HashMap<>();
    }
    
    /**
     * Calculate the average score for a user
     * @param userId The ID of the user
     * @param scores Array of numerical scores
     * @return Average score
     */
    public double calculateUserScore(int userId, double[] scores) {
        if (scores == null || scores.length == 0) {
            return 0;
        }
        double sum = 0;
        for (double score : scores) {
            sum += score;
        }
        return sum / scores.length;
    }
    
    /**
     * Get user profile information
     * @param userId The ID of the user
     * @return User profile data
     */
    public UserProfile getUserProfile(int userId) {
        return new UserProfile(
            userId, 
            "User " + userId, 
            "user" + userId + "@example.com",
            LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
        );
    }
    
    /**
     * Create a new user account
     * @param username Desired username
     * @param email User's email address
     * @param password User's password
     * @return Created user information
     */
    public CreateUserResponse createUser(String username, String email, String password) {
        int userId = users.size() + 1;
        User user = new User(userId, username, email, password);
        users.put(userId, user);
        
        return new CreateUserResponse(
            "User created successfully",
            userId,
            username,
            email
        );
    }
    
    /**
     * Authenticate user credentials
     * @param username Username
     * @param password Password
     * @return Authentication result with token
     */
    public AuthResponse authenticateUser(String username, String password) {
        // Check credentials against database
        return new AuthResponse(
            true,
            "jwt_token_here",
            3600
        );
    }
    
    /**
     * Delete a user account (admin only)
     * @param userId ID of user to delete
     * @param adminPassword Admin password for verification
     * @return Deletion status
     */
    public DeleteResponse deleteUser(int userId, String adminPassword) {
        // This is a sensitive operation that should require admin auth
        users.remove(userId);
        return new DeleteResponse("User " + userId + " deleted successfully");
    }
    
    /**
     * Calculate analytics for a date range
     * @param startDate Start date in YYYY-MM-DD format
     * @param endDate End date in YYYY-MM-DD format
     * @param metrics List of metrics to calculate
     * @return Analytics data
     */
    public AnalyticsResponse calculateAnalytics(String startDate, String endDate, String[] metrics) {
        if (metrics == null) {
            metrics = new String[]{"users", "sessions", "revenue"};
        }
        
        Map<String, Integer> analyticsData = new HashMap<>();
        for (String metric : metrics) {
            analyticsData.put(metric, (int)(Math.random() * 1000));
        }
        
        return new AnalyticsResponse(
            startDate + " to " + endDate,
            analyticsData,
            LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
        );
    }
}

// Helper classes
class User {
    private int id;
    private String username;
    private String email;
    private String password;
    
    public User(int id, String username, String email, String password) {
        this.id = id;
        this.username = username;
        this.email = email;
        this.password = password;
    }
    
    // Getters and setters would be here
}

class UserProfile {
    public int id;
    public String name;
    public String email;
    public String createdAt;
    
    public UserProfile(int id, String name, String email, String createdAt) {
        this.id = id;
        this.name = name;
        this.email = email;
        this.createdAt = createdAt;
    }
}

class CreateUserResponse {
    public String message;
    public int userId;
    public String username;
    public String email;
    
    public CreateUserResponse(String message, int userId, String username, String email) {
        this.message = message;
        this.userId = userId;
        this.username = username;
        this.email = email;
    }
}

class AuthResponse {
    public boolean authenticated;
    public String token;
    public int expiresIn;
    
    public AuthResponse(boolean authenticated, String token, int expiresIn) {
        this.authenticated = authenticated;
        this.token = token;
        this.expiresIn = expiresIn;
    }
}

class DeleteResponse {
    public String message;
    
    public DeleteResponse(String message) {
        this.message = message;
    }
}

class AnalyticsResponse {
    public String period;
    public Map<String, Integer> metrics;
    public String generatedAt;
    
    public AnalyticsResponse(String period, Map<String, Integer> metrics, String generatedAt) {
        this.period = period;
        this.metrics = metrics;
        this.generatedAt = generatedAt;
    }
}
