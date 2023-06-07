    #!/bin/bash
    #dump.sh
    mysql -uroot -p12345678 test_db < /docker-entrypoint-initdb.d/test_dump.sql
    #end of dump.sh