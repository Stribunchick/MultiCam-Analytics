import sqlite3

c = sqlite3.connect("./db/logs.db")

cur = c.cursor()

for i in range(100):
    name = f"test{i}"

    # cur.execute("""
    #     INSERT INTO configs (name, cameras_per_row, enabled, conf_thresh, fps) VALUES (?, 4, 1, 0.7, 24)
    # """, (name,))

    cur.execute("""
        INSERT INTO cameras (name, location) VALUES (?, 'corridor')
    """, (name,))
    c.commit()
    