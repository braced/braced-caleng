import time
from caleng.connections.P001 import P001_EC3
from caleng.connections.P002 import P002_EC3
from caleng.connections.P003 import P003_EC3
from caleng.connections.P004 import P004_EC3
from caleng.connections.S001 import S001_EC3
from caleng.connections.S002 import S002_EC3
from caleng.connections.S003 import S003_EC3
from caleng.connections.S004 import S004_EC3
from caleng.connections.S005 import S005_EC3
from caleng.connections.S006 import S006_EC3
from caleng.connections.S007 import S007_EC3
from caleng.connections.S008 import S008_EC3_Conn
from caleng.connections.S009 import S009_EC3
from caleng.connections.S010 import S010_EC3_Conn


def solve_connection(conn):
    if conn.enginesheet == 'P001' and conn.code == 'EC3':
        rp = P001_EC3(conn)
    elif conn.enginesheet == 'P002' and conn.code == 'EC3':
        rp = P002_EC3(conn)
    elif conn.enginesheet == 'P003' and conn.code == 'EC3':
        rp = P003_EC3(conn)
    elif conn.enginesheet == 'P004' and conn.code == 'EC3':
        rp = P004_EC3(conn)
    elif conn.enginesheet == 'S001' and conn.code == 'EC3':
        rp = S001_EC3(conn)
    elif conn.enginesheet == 'S002' and conn.code == 'EC3':
        rp = S002_EC3(conn)
    elif conn.enginesheet == 'S003' and conn.code == 'EC3':
        rp = S003_EC3(conn)
    elif conn.enginesheet == 'S004' and conn.code == 'EC3':
        rp = S004_EC3(conn)
    elif conn.enginesheet == 'S005' and conn.code == 'EC3':
        rp = S005_EC3(conn)
    elif conn.enginesheet == 'S006' and conn.code == 'EC3':
        rp = S006_EC3(conn)
    elif conn.enginesheet == 'S007' and conn.code == 'EC3':
        rp = S007_EC3(conn)
    elif conn.enginesheet == 'S008' and conn.code == 'EC3':
        # class based solver !
        c = S008_EC3_Conn(conn)
        c.setup()
        rp = c.check_and_report()
    elif conn.enginesheet == 'S009' and conn.code == 'EC3':
        rp = S009_EC3(conn)
    elif conn.enginesheet == 'S010' and conn.code == 'EC3':
        # class based solver !
        c = S010_EC3_Conn(conn)
        c.setup()
        rp = c.check_and_report()
    else:
        print("SOLVER NOT FOUND FOR:", conn.enginesheet, conn.code)
        time.sleep(1)
        return

    # Now report is saved to the cache by uuid
    rp.to_cache_by_uuid()
