const sqlite3 = require('sqlite3').verbose();

class Database {
    constructor(filename) {
        this.connection = new sqlite3.Database(filename);
    }

    run(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.connection.run(sql, params, function (err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    get(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.connection.get(sql, params, (err, row) => {
                if (err) return reject(err);
                resolve(row);
            });
        });
    }

    all(sql, params = []) {
        return new Promise((resolve, reject) => {
            this.connection.all(sql, params, (err, rows) => {
                if (err) return reject(err);
                resolve(rows);
            });
        });
    }
}

module.exports = Database;
