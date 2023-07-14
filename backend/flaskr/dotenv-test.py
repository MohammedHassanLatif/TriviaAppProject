from os import environ as env 
from dotenv import load_dotenv

load_dotenv()

print('DB_NAME: {}'.format(env['DB_NAME']))
print('DB_USER: {}'.format(env['DB_USER']))
print('DB_PASSWORD: {}'.format(env['DB_PASSWORD']))
