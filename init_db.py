import psycopg2
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

def init_database():
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()
    
    # Criar tabela de usuários
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Criar tabela de produtos
    cur.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(255) NOT NULL,
            descricao TEXT,
            preco DECIMAL(10,2) NOT NULL,
            imagem_url VARCHAR(500),
            categoria VARCHAR(100) NOT NULL,
            caracteristicas TEXT,
            em_oferta BOOLEAN DEFAULT FALSE,
            ativo BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Criar tabela de pacotes
    cur.execute('''
        CREATE TABLE IF NOT EXISTS pacotes (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            produtos_ids INTEGER[],
            total DECIMAL(10,2),
            desconto DECIMAL(5,2),
            total_final DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Inserir usuário admin padrão
    admin_password = generate_password_hash('admin123')
    cur.execute('''
        INSERT INTO users (email, password, name, is_admin) 
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (email) DO NOTHING
    ''', ('admin@techoutsourcing.com.br', admin_password, 'Administrador', True))
    
    # Inserir alguns produtos de exemplo
    produtos_exemplo = [
        ('Impressora Laser HP LaserJet Pro', 
         'Impressora monocromática de alta velocidade para escritórios. Ideal para impressão de documentos em grande volume com qualidade profissional.',
         1299.00,
         'https://via.placeholder.com/300x200',
         'impressoras',
         'Até 30 páginas por minuto|Conexão Wi-Fi e Ethernet|Impressão automática frente e verso|Toner de alta capacidade',
         False),
        
        ('Multifuncional Epson EcoTank L6190',
         'Sistema de tanque de tinta que reduz drasticamente os custos de impressão. Imprime, copia e digitaliza com alta qualidade.',
         1899.00,
         'https://via.placeholder.com/300x200',
         'multifuncionais',
         'Sistema de tanque de tinta|Impressão, cópia e digitalização|Wi-Fi Direct e Ethernet|Até 2 anos de tinta inclusa',
         True),
        
        ('Scanner Documental Fujitsu fi-7460',
         'Scanner de alta velocidade para digitalização em massa de documentos. Ideal para escritórios que precisam digitalizar grandes volumes.',
         2450.00,
         'https://via.placeholder.com/300x200',
         'scanners',
         'Até 40 páginas por minuto|Alimentador automático de 50 folhas|OCR integrado para texto pesquisável|Resolução de até 600 dpi',
         False)
    ]
    
    for produto in produtos_exemplo:
        cur.execute('''
            INSERT INTO produtos (nome, descricao, preco, imagem_url, categoria, caracteristicas, em_oferta)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        ''', produto)
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("Banco de dados inicializado com sucesso!")

if __name__ == '__main__':
    init_database()