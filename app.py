from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import os
from dotenv import load_dotenv
import ssl

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Classe User para Flask-Login
class User(UserMixin):
    def __init__(self, id, email, name, is_admin):
        self.id = id
        self.email = email
        self.name = name
        self.is_admin = is_admin

# Conexão com o banco de dados PostgreSQL Neon
def get_db_connection():
    try:
        database_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        print(f"Erro ao conectar com o banco: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if conn is None:
        print("Não foi possível conectar ao banco para inicialização")
        return
    
    cur = conn.cursor()
    
    try:
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
                cliente_id INTEGER REFERENCES users(id),
                volume_folhas VARCHAR(50) NOT NULL,
                tipo_equipamento VARCHAR(100) NOT NULL,
                tipo_impressao VARCHAR(50) NOT NULL,
                periodo_contrato VARCHAR(50) NOT NULL,
                produtos_selecionados INTEGER[],
                total DECIMAL(10,2),
                status VARCHAR(50) DEFAULT 'pendente',
                observacoes TEXT,
                observacoes_admin TEXT,
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
        
        # Inserir produtos reais com imagens reais
        produtos_exemplo = [
            # Impressoras Laser
            ('HP LaserJet Pro MFP M428fdw', 
             'Multifuncional laser monocromática com digitalização duplex automática. Ideal para pequenos escritórios que precisam de eficiência e confiabilidade.',
             1899.00,
             'https://images.unsplash.com/photo-1558756520-22cfe5d382ca?w=400&h=300&fit=crop',
             'impressoras',
             'Laser monocromática|Velocidade: 28 ppm|Resolução: 600x600 dpi|Wi-Fi, Ethernet|Display touch 5"',
             False),
            
            ('Brother HL-L8360CDW',
             'Impressora laser colorida compacta com conectividade wireless. Produza documentos coloridos vibrantes com baixo custo operacional.',
             2199.00,
             'https://images.unsplash.com/photo-1598257006675-57dafe41c932?w=400&h=300&fit=crop',
             'impressoras',
             'Laser colorida|Velocidade: 31 ppm|Resolução: 2400x600 dpi|Wi-Fi Direct|Toner alta capacidade',
             True),
            
            # Scanners
            ('Fujitsu ScanSnap iX1600',
             'Scanner documental com alimentador automático de 50 páginas. Digitalize rapidamente pilhas de documentos com qualidade profissional.',
             2450.00,
             'https://images.unsplash.com/photo-1587825140708-dfaf72ae4b04?w=400&h=300&fit=crop',
             'scanners',
             'Velocidade: 40 ppm|Alimentador: 50 folhas|Resolução: 600 dpi|Wi-Fi, USB-C|OCR inteligente',
             False),
            
            ('Epson WorkForce DS-790WN',
             'Scanner sem fio com alimentador automático duplex. Digitalize frente e verso simultaneamente com incrível velocidade.',
             1899.00,
             'https://images.unsplash.com/photo-1571667234876-45f6bef75b6a?w=400&h=300&fit=crop',
             'scanners',
             'Velocidade: 35 ppm|Duplex automático|Resolução: 600 dpi|Wi-Fi, Ethernet|Display LCD',
             True),
            
            # Multifuncionais
            ('Epson EcoTank L6190',
             'Multifuncional com sistema de tanque de tinta que reduz custos em até 90%. Imprime, copia e digitaliza com economia extraordinária.',
             1699.00,
             'https://images.unsplash.com/photo-1558756520-22cfe5d382ca?w=400&h=300&fit=crop',
             'multifuncionais',
             'Tanque de tinta|Impressão, cópia, digitalização|Wi-Fi Direct|Tinta para 2 anos|Cartucho-free',
             True),
            
            ('Brother MFC-L8900CDW',
             'Multifuncional laser colorida para escritórios de médio porte. Alta produtividade com custo operacional reduzido.',
             2899.00,
             'https://images.unsplash.com/photo-1562408590-e32931084e23?w=400&h=300&fit=crop',
             'multifuncionais',
             'Laser colorida|Velocidade: 33 ppm|Resolução: 2400x600 dpi|Wi-Fi, Ethernet|Display touch 10.1"',
             False)
        ]
        
        for produto in produtos_exemplo:
            cur.execute('''
                INSERT INTO produtos (nome, descricao, preco, imagem_url, categoria, caracteristicas, em_oferta)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            ''', produto)
        
        conn.commit()
        print("✅ Banco de dados inicializado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    if conn is None:
        return None
        
    cur = conn.cursor()
    try:
        cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        user = cur.fetchone()
        
        if user:
            return User(id=user[0], email=user[1], name=user[3], is_admin=user[4])
        return None
    except Exception as e:
        print(f"Erro ao carregar usuário: {e}")
        return None
    finally:
        cur.close()
        conn.close()

# Rotas públicas
@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Buscar produtos ativos (limite de 6 para a página inicial)
    cur.execute('SELECT * FROM produtos WHERE ativo = TRUE LIMIT 6')
    produtos = cur.fetchall()
    cur.close()
    conn.close()
    
    # Converter para lista de dicionários
    produtos_list = []
    for prod in produtos:
        produtos_list.append({
            'id': prod[0],
            'nome': prod[1],
            'descricao': prod[2],
            'preco': float(prod[3]),
            'imagem_url': prod[4],
            'categoria': prod[5],
            'caracteristicas': prod[6],
            'em_oferta': prod[7]
        })
    
    return render_template('index.html', produtos=produtos_list)

@app.route('/produtos')
def produtos():
    categoria = request.args.get('categoria', '')
    conn = get_db_connection()
    if conn is None:
        return render_template('produtos.html', produtos=[], categoria=categoria)
        
    cur = conn.cursor()
    try:
        if categoria:
            cur.execute('SELECT * FROM produtos WHERE categoria = %s AND ativo = TRUE', (categoria,))
        else:
            cur.execute('SELECT * FROM produtos WHERE ativo = TRUE')
        
        produtos = cur.fetchall()
        
        produtos_list = []
        for prod in produtos:
            produtos_list.append({
                'id': prod[0],
                'nome': prod[1],
                'descricao': prod[2],
                'preco': float(prod[3]),
                'imagem_url': prod[4],
                'categoria': prod[5],
                'caracteristicas': prod[6],
                'em_oferta': prod[7]
            })
        
        return render_template('produtos.html', produtos=produtos_list, categoria=categoria)
    except Exception as e:
        print(f"Erro ao carregar produtos: {e}")
        return render_template('produtos.html', produtos=[], categoria=categoria)
    finally:
        cur.close()
        conn.close()

@app.route('/ofertas')
def ofertas():
    conn = get_db_connection()
    if conn is None:
        return render_template('ofertas.html', produtos=[])
        
    cur = conn.cursor()
    try:
        cur.execute('SELECT * FROM produtos WHERE em_oferta = TRUE AND ativo = TRUE')
        produtos = cur.fetchall()
        
        produtos_list = []
        for prod in produtos:
            produtos_list.append({
                'id': prod[0],
                'nome': prod[1],
                'descricao': prod[2],
                'preco': float(prod[3]),
                'imagem_url': prod[4],
                'categoria': prod[5],
                'caracteristicas': prod[6],
                'em_oferta': prod[7]
            })
        
        return render_template('ofertas.html', produtos=produtos_list)
    except Exception as e:
        print(f"Erro ao carregar ofertas: {e}")
        return render_template('ofertas.html', produtos=[])
    finally:
        cur.close()
        conn.close()
        
        
@app.route('/pacotes')
@login_required
def pacotes():
    """Página para clientes criarem pacotes personalizados"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM produtos WHERE ativo = TRUE')
    produtos = cur.fetchall()
    cur.close()
    conn.close()
    
    produtos_por_categoria = {}
    for prod in produtos:
        categoria = prod[5]
        if categoria not in produtos_por_categoria:
            produtos_por_categoria[categoria] = []
        
        produtos_por_categoria[categoria].append({
            'id': prod[0],
            'nome': prod[1],
            'descricao': prod[2],
            'preco': float(prod[3]),
            'imagem_url': prod[4],
            'categoria': prod[5],
            'caracteristicas': prod[6],
            'em_oferta': prod[7]
        })
    
    return render_template('pacotes.html', produtos_por_categoria=produtos_por_categoria)

@app.route('/solicitar_pacote', methods=['GET', 'POST'])
@login_required
def solicitar_pacote():
    """Solicitar um pacote personalizado"""
    if request.method == 'GET':
        return render_template('solicitar_pacote.html')
    
    if request.method == 'POST':
        try:
            volume_folhas = request.form['volume_folhas']
            tipo_impressao = request.form['tipo_impressao']
            cor_impressao = request.form['cor_impressao']
            velocidade = request.form['velocidade']
            orcamento = request.form['orcamento']
            observacoes = request.form['observacoes']
            produtos_selecionados = request.form.getlist('produtos')
            
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Calcular total dos produtos selecionados
            total = 0
            if produtos_selecionados:
                placeholders = ','.join(['%s'] * len(produtos_selecionados))
                cur.execute(f'SELECT SUM(preco) FROM produtos WHERE id IN ({placeholders})', 
                           produtos_selecionados)
                total = cur.fetchone()[0] or 0
            
            # Aplicar desconto progressivo
            desconto = 0
            if len(produtos_selecionados) >= 3:
                desconto = 0.1
            if len(produtos_selecionados) >= 5:
                desconto = 0.15
            if len(produtos_selecionados) >= 7:
                desconto = 0.2
            
            total_final = total * (1 - desconto)
            
            # Inserir pacote - CORRIGIDO: usar user_id em vez de cliente_id
            cur.execute('''
                INSERT INTO pacotes (user_id, produtos_ids, volume_folhas_mes, tipo_impressao, 
                                   cor_impressao, velocidade_necessaria, orcamento_maximo, 
                                   observacoes, total, desconto, total_final)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (current_user.id, produtos_selecionados, volume_folhas, tipo_impressao,
                  cor_impressao, velocidade, orcamento, observacoes, total, desconto, total_final))
            
            conn.commit()
            cur.close()
            conn.close()
            
            flash('Pacote solicitado com sucesso! Entraremos em contato em breve.', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'Erro ao solicitar pacote: {str(e)}', 'danger')
            return render_template('solicitar_pacote.html')

@app.route('/meus_pacotes')
@login_required
def meus_pacotes():
    """Visualizar pacotes do usuário"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    if current_user.is_admin:
        # Admin vê todos os pacotes
        cur.execute('''
            SELECT p.*, u.name as cliente_nome, u.email 
            FROM pacotes p 
            JOIN users u ON p.user_id = u.id 
            ORDER BY p.created_at DESC
        ''')
    else:
        # Cliente vê apenas seus pacotes
        cur.execute('''
            SELECT * FROM pacotes 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        ''', (current_user.id,))
    
    pacotes = cur.fetchall()
    cur.close()
    conn.close()
    
    pacotes_list = []
    for pac in pacotes:
        pacotes_list.append({
            'id': pac[0],
            'user_id': pac[1],
            'produtos_ids': pac[2],
            'volume_folhas_mes': pac[3],
            'tipo_impressao': pac[4],
            'cor_impressao': pac[5],
            'velocidade_necessaria': pac[6],
            'orcamento_maximo': float(pac[7]) if pac[7] else None,
            'observacoes': pac[8],
            'status': pac[9],
            'total': float(pac[10]) if pac[10] else None,
            'desconto': float(pac[11]) if pac[11] else None,
            'total_final': float(pac[12]) if pac[12] else None,
            'created_at': pac[13],
            'cliente_nome': pac[14] if len(pac) > 14 else current_user.name
        })
    
    return render_template('meus_pacotes.html', pacotes=pacotes_list, is_admin=current_user.is_admin)

# Rota para admin gerenciar pacotes
@app.route('/admin/pacotes')
@login_required
def admin_pacotes():
    if not current_user.is_admin:
        flash('Acesso negado. Área restrita para administradores.', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if conn is None:
        return render_template('admin_pacotes.html', pacotes=[], produtos=[])
        
    cur = conn.cursor()
    try:
        # Buscar pacotes
        cur.execute('''
            SELECT p.*, u.name as cliente_nome, u.email as cliente_email 
            FROM pacotes p 
            LEFT JOIN users u ON p.cliente_id = u.id 
            ORDER BY p.created_at DESC
        ''')
        pacotes = cur.fetchall()
        
        # Buscar produtos para o formulário
        cur.execute('SELECT * FROM produtos WHERE ativo = TRUE')
        produtos = cur.fetchall()
        
        pacotes_list = []
        for pac in pacotes:
            pacotes_list.append({
                'id': pac[0],
                'cliente_nome': pac[11],
                'cliente_email': pac[12],
                'volume_folhas': pac[2],
                'tipo_equipamento': pac[3],
                'tipo_impressao': pac[4],
                'periodo_contrato': pac[5],
                'produtos_selecionados': pac[6],
                'total': float(pac[7]) if pac[7] else 0,
                'status': pac[8],
                'observacoes': pac[9],
                'observacoes_admin': pac[10],
                'created_at': pac[13]
            })
        
        produtos_list = []
        for prod in produtos:
            produtos_list.append({
                'id': prod[0],
                'nome': prod[1],
                'preco': float(prod[3]),
                'categoria': prod[5]
            })
        
        return render_template('admin_pacotes.html', pacotes=pacotes_list, produtos=produtos_list)
    except Exception as e:
        print(f"Erro ao carregar pacotes: {e}")
        return render_template('admin_pacotes.html', pacotes=[], produtos=[])
    finally:
        cur.close()
        conn.close()

# Rota para admin criar proposta de pacote
@app.route('/admin/criar_proposta/<int:pacote_id>', methods=['GET', 'POST'])
@login_required
def criar_proposta(pacote_id):
    if not current_user.is_admin:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    if conn is None:
        flash('Erro de conexão com o banco.', 'danger')
        return redirect(url_for('admin_pacotes'))
    
    if request.method == 'POST':
        produtos_ids = request.form.getlist('produtos_ids')
        total = request.form['total']
        observacoes_admin = request.form.get('observacoes_admin', '')
        
        cur = conn.cursor()
        try:
            # Atualizar pacote com produtos e total
            cur.execute('''
                UPDATE pacotes 
                SET produtos_selecionados = %s, total = %s, observacoes_admin = %s, status = 'proposto'
                WHERE id = %s
            ''', (produtos_ids, total, observacoes_admin, pacote_id))
            
            conn.commit()
            flash('Proposta de pacote enviada com sucesso!', 'success')
            return redirect(url_for('admin_pacotes'))
        except Exception as e:
            print(f"Erro ao criar proposta: {e}")
            flash('Erro ao criar proposta.', 'danger')
        finally:
            cur.close()
            conn.close()
    
    # Buscar dados do pacote
    cur = conn.cursor()
    try:
        cur.execute('''
            SELECT p.*, u.name as cliente_nome 
            FROM pacotes p 
            LEFT JOIN users u ON p.cliente_id = u.id 
            WHERE p.id = %s
        ''', (pacote_id,))
        pacote = cur.fetchone()
        
        cur.execute('SELECT * FROM produtos WHERE ativo = TRUE')
        produtos = cur.fetchall()
        
        pacote_dict = {
            'id': pacote[0],
            'cliente_nome': pacote[11],
            'volume_folhas': pacote[2],
            'tipo_equipamento': pacote[3],
            'tipo_impressao': pacote[4],
            'periodo_contrato': pacote[5],
            'observacoes': pacote[9]
        }
        
        produtos_list = []
        for prod in produtos:
            produtos_list.append({
                'id': prod[0],
                'nome': prod[1],
                'preco': float(prod[3]),
                'categoria': prod[5]
            })
        
        return render_template('criar_proposta.html', 
                             pacote=pacote_dict, 
                             produtos=produtos_list)
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        flash('Erro ao carregar dados.', 'danger')
        return redirect(url_for('admin_pacotes'))
    finally:
        cur.close()
        conn.close()

# Área administrativa - ADICIONE ESTAS ROTAS
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Acesso negado. Área restrita para administradores.', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM produtos ORDER BY id')
    produtos = cur.fetchall()
    cur.close()
    conn.close()
    
    produtos_list = []
    for prod in produtos:
        produtos_list.append({
            'id': prod[0],
            'nome': prod[1],
            'descricao': prod[2],
            'preco': float(prod[3]),
            'imagem_url': prod[4],
            'categoria': prod[5],
            'caracteristicas': prod[6],
            'em_oferta': prod[7],
            'ativo': prod[8]
        })
    
    return render_template('admin.html', produtos=produtos_list)

@app.route('/admin/produto/novo', methods=['GET', 'POST'])
@login_required
def novo_produto():
    if not current_user.is_admin:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        preco = request.form['preco']
        imagem_url = request.form['imagem_url']
        categoria = request.form['categoria']
        caracteristicas = request.form['caracteristicas']
        em_oferta = 'em_oferta' in request.form
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            '''INSERT INTO produtos (nome, descricao, preco, imagem_url, categoria, caracteristicas, em_oferta, ativo)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
            (nome, descricao, preco, imagem_url, categoria, caracteristicas, em_oferta, True)
        )
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Produto criado com sucesso!', 'success')
        return redirect(url_for('admin'))
    
    return render_template('editar_produto.html')

@app.route('/admin/produto/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_produto(id):
    if not current_user.is_admin:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        preco = request.form['preco']
        imagem_url = request.form['imagem_url']
        categoria = request.form['categoria']
        caracteristicas = request.form['caracteristicas']
        em_oferta = 'em_oferta' in request.form
        ativo = 'ativo' in request.form
        
        cur.execute(
            '''UPDATE produtos SET nome = %s, descricao = %s, preco = %s, imagem_url = %s,
               categoria = %s, caracteristicas = %s, em_oferta = %s, ativo = %s
               WHERE id = %s''',
            (nome, descricao, preco, imagem_url, categoria, caracteristicas, em_oferta, ativo, id)
        )
        conn.commit()
        cur.close()
        conn.close()
        
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('admin'))
    
    cur.execute('SELECT * FROM produtos WHERE id = %s', (id,))
    produto = cur.fetchone()
    cur.close()
    conn.close()
    
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('admin'))
    
    produto_dict = {
        'id': produto[0],
        'nome': produto[1],
        'descricao': produto[2],
        'preco': float(produto[3]),
        'imagem_url': produto[4],
        'categoria': produto[5],
        'caracteristicas': produto[6],
        'em_oferta': produto[7],
        'ativo': produto[8]
    }
    
    return render_template('editar_produto.html', produto=produto_dict)

@app.route('/admin/produto/excluir/<int:id>')
@login_required
def excluir_produto(id):
    if not current_user.is_admin:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM produtos WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Produto excluído com sucesso!', 'success')
    return redirect(url_for('admin'))

# API para calcular pacote
@app.route('/api/calcular_pacote', methods=['POST'])
@login_required
def calcular_pacote():
    try:
        data = request.get_json()
        produtos_ids = data.get('produtos', [])
        volume_folhas = data.get('volume_folhas', '1000-5000')
        periodo_contrato = data.get('periodo_contrato', 'anual')
        
        conn = get_db_connection()
        if conn is None:
            return jsonify({'success': False, 'message': 'Erro de conexão'})
            
        cur = conn.cursor()
        
        # Calcular custo dos produtos
        custo_produtos = 0
        for prod_id in produtos_ids:
            cur.execute('SELECT preco FROM produtos WHERE id = %s', (prod_id,))
            produto = cur.fetchone()
            if produto:
                custo_produtos += float(produto[0])
        
        # Calcular custo mensal baseado no volume e período
        custo_mensal = calcular_custo_mensal(volume_folhas, periodo_contrato)
        
        # Calcular total (produtos + 12 meses de serviço)
        total = custo_produtos + (custo_mensal * 12)
        
        # Aplicar desconto para contratos anuais
        if periodo_contrato == 'anual':
            total *= 0.9  # 10% de desconto
        
        return jsonify({
            'success': True,
            'total': round(total, 2),
            'custo_produtos': round(custo_produtos, 2),
            'custo_mensal': round(custo_mensal, 2),
            'desconto': 10 if periodo_contrato == 'anual' else 0
        })
    except Exception as e:
        print(f"Erro ao calcular pacote: {e}")
        return jsonify({'success': False, 'message': 'Erro interno'})

def calcular_custo_mensal(volume_folhas, periodo_contrato):
    """Calcula o custo mensal baseado no volume de folhas"""
    custos = {
        '1000-5000': 50,
        '5000-10000': 80,
        '10000-20000': 120,
        '20000-50000': 200,
        '50000+': 350
    }
    
    custo_base = custos.get(volume_folhas, 50)
    
    # Ajustar custo baseado no período
    if periodo_contrato == 'trimestral':
        return custo_base * 1.2  # 20% mais caro
    elif periodo_contrato == 'anual':
        return custo_base * 0.9  # 10% mais barato
    
    return custo_base

# Rotas de autenticação
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn is None:
            flash('Erro de conexão com o banco de dados.', 'danger')
            return render_template('login.html')
            
        cur = conn.cursor()
        try:
            cur.execute('SELECT * FROM users WHERE email = %s', (email,))
            user = cur.fetchone()
            
            if user and check_password_hash(user[2], password):
                user_obj = User(id=user[0], email=user[1], name=user[3], is_admin=user[4])
                login_user(user_obj)
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Email ou senha incorretos.', 'danger')
        except Exception as e:
            print(f"Erro no login: {e}")
            flash('Erro interno do servidor.', 'danger')
        finally:
            cur.close()
            conn.close()
    
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn is None:
            flash('Erro de conexão com o banco de dados.', 'danger')
            return render_template('registro.html')
            
        cur = conn.cursor()
        try:
            # Verificar se email já existe
            cur.execute('SELECT id FROM users WHERE email = %s', (email,))
            if cur.fetchone():
                flash('Email já cadastrado.', 'danger')
                return render_template('registro.html')
            
            # Criar novo usuário
            hashed_password = generate_password_hash(password)
            cur.execute(
                'INSERT INTO users (email, password, name, is_admin) VALUES (%s, %s, %s, %s)',
                (email, hashed_password, name, False)
            )
            conn.commit()
            flash('Conta criada com sucesso! Faça login para continuar.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            print(f"Erro no registro: {e}")
            flash('Erro ao criar conta.', 'danger')
        finally:
            cur.close()
            conn.close()
    
    return render_template('registro.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso.', 'info')
    return redirect(url_for('index'))

# Rota para teste de conexão com o banco
@app.route('/test-db')
def test_db():
    conn = get_db_connection()
    if conn:
        conn.close()
        return "✅ Conexão com o banco OK!"
    else:
        return "❌ Falha na conexão com o banco"

if __name__ == '__main__':
    print("🚀 Inicializando servidor...")
    print(f"📝 SECRET_KEY carregada: {'Sim' if app.config['SECRET_KEY'] else 'Não'}")
    
    # Testar conexão com banco
    conn = get_db_connection()
    if conn:
        print("✅ Conectado ao PostgreSQL Neon!")
        conn.close()
    else:
        print("❌ Falha ao conectar com PostgreSQL")
    
    init_db()
    print("🌐 Servidor iniciado! Acesse: http://localhost:5000")
    print("🔑 Admin: admin@techoutsourcing.com.br / admin123")
    app.run(debug=True)