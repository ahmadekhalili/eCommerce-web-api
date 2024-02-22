### Add .env in root of project with this structure:  
```
SECRET_KEY=-l(24ils3ph2mp0%cguxdq!i%8cfjfldw*1ugu+a@9wk^2x^-e  # replace your project secret key  
POSTGRES_MY_HOST=127.0.0.1
POSTGRES_DBNAME=
POSTGRES_USERNAME=
POSTGRES_USERPASS=
MONGO_HOST=127.0.0.1
MONGO_DBNAME=
MONGO_SOURCE=admin
MONGO_USERNAME=
MONGO_USERPASS=
MONGO_ADMINUSER=
```

Create postgres and mongo db with that informations.  

**Note**: SECRET_KEY is django settings/SECRET_KEY. provided default value works fine but recommended to replace with your project SECRET_KEY.  