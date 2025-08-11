/**
 * Sample JavaScript file for Code2API demonstration
 */

function calculateUserScore(userId, scores) {
    /**
     * Calculate the average score for a user
     * @param {number} userId - The ID of the user
     * @param {number[]} scores - Array of numerical scores
     * @returns {number} Average score
     */
    if (!scores || scores.length === 0) {
        return 0;
    }
    return scores.reduce((a, b) => a + b, 0) / scores.length;
}

async function getUserProfile(userId) {
    /**
     * Get user profile information
     * @param {number} userId - The ID of the user
     * @returns {Promise<Object>} User profile data
     */
    return {
        id: userId,
        name: `User ${userId}`,
        email: `user${userId}@example.com`,
        createdAt: new Date().toISOString()
    };
}

const sendNotification = async (userId, message, notificationType = 'email') => {
    /**
     * Send a notification to a user
     * @param {number} userId - The ID of the user
     * @param {string} message - The notification message
     * @param {string} notificationType - Type of notification
     * @returns {Promise<Object>} Notification status
     */
    return {
        status: 'sent',
        userId,
        type: notificationType,
        message,
        timestamp: new Date().toISOString()
    };
};

class UserManager {
    constructor() {
        this.users = new Map();
    }

    createUser(username, email, password) {
        /**
         * Create a new user account
         * @param {string} username - Desired username
         * @param {string} email - User's email address
         * @param {string} password - User's password
         * @returns {Object} Created user information
         */
        const user = {
            id: Date.now(),
            username,
            email,
            createdAt: new Date().toISOString()
        };
        
        this.users.set(user.id, user);
        
        return {
            message: 'User created successfully',
            user: { ...user, password: undefined }
        };
    }

    async authenticateUser(username, password) {
        /**
         * Authenticate user credentials
         * @param {string} username - Username
         * @param {string} password - Password
         * @returns {Promise<Object>} Authentication result with token
         */
        // Check credentials against database
        return {
            authenticated: true,
            token: 'jwt_token_here',
            expiresIn: 3600
        };
    }

    deleteUser(userId, adminPassword) {
        /**
         * Delete a user account (admin only)
         * @param {number} userId - ID of user to delete
         * @param {string} adminPassword - Admin password for verification
         * @returns {Object} Deletion status
         */
        this.users.delete(userId);
        return { message: `User ${userId} deleted successfully` };
    }
}

function calculateAnalytics(startDate, endDate, metrics = ['users', 'sessions', 'revenue']) {
    /**
     * Calculate analytics for a date range
     * @param {string} startDate - Start date in YYYY-MM-DD format
     * @param {string} endDate - End date in YYYY-MM-DD format
     * @param {string[]} metrics - List of metrics to calculate
     * @returns {Object} Analytics data
     */
    const analyticsData = {};
    
    metrics.forEach(metric => {
        analyticsData[metric] = Math.floor(Math.random() * 1000);
    });
    
    return {
        period: `${startDate} to ${endDate}`,
        metrics: analyticsData,
        generatedAt: new Date().toISOString()
    };
}

// Export functions for Node.js if running in Node environment
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        calculateUserScore,
        getUserProfile,
        sendNotification,
        UserManager,
        calculateAnalytics
    };
}
