import pyodbc
import hashlib

def get_connection():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=localhost,1433;'
        'DATABASE=ДеканатКалькулятор;'
        'UID=pavelchen;'
        'PWD=523604;'
    )

def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """
    Выполнение SQL-запросов с параметрами
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        if fetch_one:
            return cursor.fetchone()
        elif fetch_all:
            return cursor.fetchall()
        else:
            conn.commit()
            return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()