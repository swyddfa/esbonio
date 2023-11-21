from esbonio.sphinx_agent.app import Database


def test_ensure_table_new():
    """Ensure that we can create a table where none existed previously."""

    table = Database.Table(
        "example",
        [
            Database.Column(name="name", dtype="TEXT"),
            Database.Column(name="age", dtype="INTEGER"),
        ],
    )

    database = Database(":memory:")
    database.ensure_table(table)

    cursor = database.db.execute("PRAGMA table_info(example);")
    rows = cursor.fetchall()

    assert rows[0] == (0, "name", "TEXT", 0, None, 0)
    assert rows[1] == (1, "age", "INTEGER", 0, None, 0)


def test_ensure_table_existing():
    """Ensure that ``ensure_table`` is a no-op if the table already exists and is
    compatible with the given definition."""

    table = Database.Table(
        "example",
        [
            Database.Column(name="name", dtype="TEXT"),
            Database.Column(name="age", dtype="INTEGER"),
        ],
    )

    database = Database(":memory:")
    database.ensure_table(table)

    cursor = database.db.execute("PRAGMA schema_version;")
    version = cursor.fetchone()[0]
    assert version == 1

    database.ensure_table(table)

    # Schema version would be incremented if we made changes to the tables
    cursor = database.db.execute("PRAGMA schema_version;")
    version = cursor.fetchone()[0]
    assert version == 1


def test_insert_and_clear_table():
    """Ensure that we can insert values into a table and subsequently clear it."""
    table = Database.Table(
        "example",
        [
            Database.Column(name="name", dtype="TEXT"),
            Database.Column(name="age", dtype="INTEGER"),
        ],
    )

    database = Database(":memory:")
    database.ensure_table(table)
    database.insert_values(table, [("alice", 12), ("bob", 13)])

    cursor = database.db.execute("SELECT * FROM example")
    rows = cursor.fetchall()

    assert rows[0] == ("alice", 12)
    assert rows[1] == ("bob", 13)

    database.clear_table(table)

    cursor = database.db.execute("SELECT * FROM example")
    rows = cursor.fetchall()
    assert len(rows) == 0


def test_ensure_table_update():
    """Ensure that ``ensure_table`` can drop and recreate a table if the schema
    changes.."""

    table = Database.Table(
        "example",
        [
            Database.Column(name="name", dtype="TEXT"),
            Database.Column(name="age", dtype="INTEGER"),
        ],
    )

    database = Database(":memory:")
    database.ensure_table(table)

    cursor = database.db.execute("PRAGMA table_info(example);")
    rows = cursor.fetchall()

    assert rows[0] == (0, "name", "TEXT", 0, None, 0)
    assert rows[1] == (1, "age", "INTEGER", 0, None, 0)

    cursor = database.db.execute("PRAGMA schema_version;")
    version = cursor.fetchone()[0]
    assert version == 1

    table.columns.insert(1, Database.Column(name="address", dtype="TEXT"))
    database.ensure_table(table)

    cursor = database.db.execute("PRAGMA table_info(example);")
    rows = cursor.fetchall()

    assert rows[0] == (0, "name", "TEXT", 0, None, 0)
    assert rows[1] == (1, "address", "TEXT", 0, None, 0)
    assert rows[2] == (2, "age", "INTEGER", 0, None, 0)

    # Schema version would be incremented if we made changes to the tables
    cursor = database.db.execute("PRAGMA schema_version;")
    version = cursor.fetchone()[0]
    assert version == 3
