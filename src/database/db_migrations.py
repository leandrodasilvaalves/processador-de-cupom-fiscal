def _insert_migration_record(cursor, migration_name):
    cursor.execute(
        "INSERT INTO _migrations (migration_name) VALUES (%s)",
        (migration_name,),
    )


def _migration_already_exists(cursor, migration_name):
    cursor.execute(
        "SELECT COUNT(*) FROM _migrations WHERE migration_name = %s", 
        (migration_name,)
    )
    return cursor.fetchone()[0] > 0


def execute_with_migration(sql, migration_name, cursor):
    if _migration_already_exists(cursor, migration_name):
        return

    cursor.execute(sql)
    _insert_migration_record(cursor, migration_name)


def create_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS _migrations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            migration_name VARCHAR(100) NOT NULL UNIQUE,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_migration_name (migration_name)
        )
    """
    )
