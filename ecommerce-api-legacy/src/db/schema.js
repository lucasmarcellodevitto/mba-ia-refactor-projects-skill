const { hashPassword } = require('../utils/passwordHasher');

function initSchema(database) {
    database.connection.serialize(() => {
        database.connection.run("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)");
        database.connection.run("CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)");
        database.connection.run("CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)");
        database.connection.run("CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)");
        database.connection.run("CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)");

        database.connection.run(
            "INSERT INTO users (name, email, pass) VALUES (?, ?, ?)",
            ['Leonan', 'leonan@fullcycle.com.br', hashPassword('123')]
        );
        database.connection.run(
            "INSERT INTO courses (title, price, active) VALUES (?, ?, ?), (?, ?, ?)",
            ['Clean Architecture', 997.00, 1, 'Docker', 497.00, 1]
        );
        database.connection.run(
            "INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)",
            [1, 1]
        );
        database.connection.run(
            "INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)",
            [1, 997.00, 'PAID']
        );
    });
}

module.exports = { initSchema };
