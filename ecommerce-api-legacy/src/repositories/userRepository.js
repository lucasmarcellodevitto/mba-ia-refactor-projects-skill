class UserRepository {
    constructor(database) {
        this.database = database;
    }

    findIdByEmail(email) {
        return this.database.get("SELECT id FROM users WHERE email = ?", [email]);
    }

    create({ name, email, passwordHash }) {
        return this.database.run(
            "INSERT INTO users (name, email, pass) VALUES (?, ?, ?)",
            [name, email, passwordHash]
        );
    }

    deleteById(id) {
        return this.database.run("DELETE FROM users WHERE id = ?", [id]);
    }
}

module.exports = UserRepository;
