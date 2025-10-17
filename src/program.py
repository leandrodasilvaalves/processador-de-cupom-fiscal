from config.log_config import logger
from database import db_tables
from use_cases import process_pending_files, categorize_purchases
from database.db import connect, close as db_close

logger.info("Starting the application...")

db = connect()
db_tables.setup_database(db)
db_close()

process_pending_files.process()

# print("Menu de opções:")

# menu=0
# print(f'{menu}. Sair')

# menu +=1
# print(f'{menu }. Processar arquivos pendentes')

# menu +=1
# print(f'{menu}. Categorizar compras')

# menu +=1
# print(f'{menu}. Categorizar empresas')

# opcao = input("Escolha uma opção: ")
# if opcao == '1':
#     process_pending_files.process()
# elif opcao == '2':
#     categorize_purchases.process()
# else:
#     print("Saindo...")
