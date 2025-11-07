from werkzeug.security import generate_password_hash
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def fix_admin_password():
    # Gerar hash CORRETO para 'admin123'
    password_hash = generate_password_hash('admin123')
    print(f"Hash gerado: {password_hash}")
    
    # Conectar ao banco
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()
    
    # Atualizar a senha
    cur.execute(
        "UPDATE users SET password = %s WHERE email = %s",
        (password_hash, 'admin@techoutsourcing.com.br')
    )
    conn.commit()
    
    # Verificar
    cur.execute("SELECT email, password FROM users WHERE email = %s", 
                ('admin@techoutsourcing.com.br',))
    user = cur.fetchone()
    
    print(f"Email: {user[0]}")
    print(f"Senha (hash): {user[1][:50]}...")
    print("✅ Senha atualizada com sucesso!")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    fix_admin_password()