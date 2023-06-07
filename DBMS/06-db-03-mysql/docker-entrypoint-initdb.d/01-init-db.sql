-- CREATE user test-simple-user
CREATE USER 'test' IDENTIFIED WITH mysql_native_password BY 'testpass'
     WITH MAX_QUERIES_PER_HOUR 100 PASSWORD EXPIRE INTERVAL 180 DAY FAILED_LOGIN_ATTEMPTS 3
     ATTRIBUTE '{"surname": "Pretty", "name": "James"}';

-- ADD PRIVILIGE user test-simple-user to test_db
GRANT SELECT on test_db.* TO test;