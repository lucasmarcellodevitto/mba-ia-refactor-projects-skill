class AuditLogRepository {
    constructor(database) {
        this.database = database;
    }

    create(action) {
        return this.database.run(
            "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
            [action]
        );
    }
}

module.exports = AuditLogRepository;
