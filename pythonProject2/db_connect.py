import pymysql


# MariaDB 연결 설정
def connect(employee_no):
    con_ip = '34.125.15.75'  # MariaDB 서버 IP 주소
    con_port = 3307          # MariaDB 포트 번호
    con_id = '7777'          # 사용자 ID
    con_db = 'test'         # 연결할 데이터베이스 이름


    connection = pymysql.connect(host=con_ip, port=con_port, user=con_id, db=con_db, charset='utf8')
    cursor = connection.cursor()

    # SQL 쿼리에 사용자 식별자를 인자로 전달
    cursor.execute("""
            SELECT FILE_URL
            FROM test.EMPLOYEE
            WHERE NO = %s
        """, (employee_no,))

    image_url = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return image_url
