class EnrollmentRepository {
    constructor(database) {
        this.database = database;
    }

    create(userId, courseId) {
        return this.database.run(
            "INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)",
            [userId, courseId]
        );
    }
}

module.exports = EnrollmentRepository;
