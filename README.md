### Add .env in root of project with this structure:  
SECRET_KEY=-l(24ils3ph2mp0%cguxdq!i%8cfjfldw*1ugu+a@9wk^2x^-e  # replace your project secret key  
POSTGRES_NAME=  
POSTGRES_USER=  
POSTGRES_PASSWORD=  
POSTGRES_HOST=  
MONGO_NAME=  
MONGO_HOST=  
MONGO_SOURCE=  
MONGO_USER=  
MONGO_PASSWORD=  
MONGO_ADMINUSER=  

Create postgres and mongo db with that informations.  

**Note**: SECRET_KEY is django settings/SECRET_KEY. provided default value works fine but recommended to replace with your project SECRET_KEY.  
**Note**: MONGO_SOURCE in most cases is: admin