import os
import sqlite3
import types
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Stub for pandas
class FakeSeries(list):
    def sort_values(self):
        return FakeSeries(sorted(self))

    def tolist(self):
        return list(self)

class FakeDataFrame(dict):
    pass

def fake_read_sql(query, conn):
    col = query.split()[2]
    rows = [row[0] for row in conn.execute(query).fetchall()]
    return FakeDataFrame({col: FakeSeries(rows)})

pandas_stub = types.SimpleNamespace(read_sql=fake_read_sql)

# Stub for streamlit
st_stub = types.SimpleNamespace(
    secrets={},
    info=lambda *a, **k: None,
    error=lambda *a, **k: None,
    stop=lambda *a, **k: None,
    selectbox=lambda *a, **k: None,
    text_input=lambda *a, **k: None,
    expander=lambda *a, **k: types.SimpleNamespace(__enter__=lambda s: None, __exit__=lambda s,*a,**k: False),
    multiselect=lambda *a, **k: [],
    title=lambda *a, **k: None,
    write=lambda *a, **k: None,
    dataframe=lambda *a, **k: None,
    subheader=lambda *a, **k: None,
    download_button=lambda *a, **k: None,
    warning=lambda *a, **k: None,
    success=lambda *a, **k: None,
)

sys.modules['streamlit'] = st_stub
sys.modules['pandas'] = pandas_stub

import streamlit_app


def test_get_unique_sorted():
    conn = sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE job_postings (category TEXT)')
    conn.executemany(
        'INSERT INTO job_postings (category) VALUES (?)',
        [
            ('b',),
            ('a',),
            ('b',),
            ('c',),
            ('',),
            (None,),
        ],
    )
    conn.commit()
    result = streamlit_app.get_unique('category', connection=conn, table_name='job_postings')
    assert result == ['a', 'b', 'c']
