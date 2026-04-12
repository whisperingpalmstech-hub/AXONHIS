#!/bin/bash
HASH=$(sudo docker exec axonhis_backend python3 -c "import bcrypt; print(bcrypt.hashpw(b'Password123!', bcrypt.gensalt(rounds=12)).decode('utf-8'))")
echo "Updating DB with hash: $HASH"
sudo docker exec 11dffb2d738a_axonhis_postgres psql -U axonhis -d axonhis -c "UPDATE patient_accounts SET password_hash = '$HASH' WHERE email = 'suj@example.com';"

