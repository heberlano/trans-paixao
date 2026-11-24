"""Motivos de atraso fictícios, criados para o ambiente de demonstração."""
SCENARIOS = (
    ('O motorista fez uma pausa para comemorar a vitória do Flamengo. A comemoração demorou mais do que o previsto', 'Reforçar o cumprimento das janelas de entrega e organizar pausas sem comprometer o prazo.'),
    ('O motorista precisou levar a avó ao treino de jiu-jítsu e aguardou o fim da aula', 'Prever um motorista substituto quando surgirem compromissos pessoais.'),
    ('Um bode se recusou a sair da frente do caminhão e a equipe precisou esperar a passagem ficar livre', 'Orientar a equipe a comunicar obstáculos e avaliar rotas alternativas seguras.'),
    ('O motorista parou para tomar um café e acabou entrando em uma longa discussão sobre futebol', 'Alinhar a duração das pausas e monitorar as janelas de entrega.'),
    ('O GPS mandou entrar em uma estrada que terminava em um galinheiro. Foi necessário retornar à rota correta', 'Conferir os trajetos antes da saída e manter rotas alternativas.'),
    ('Uma festa de aniversário improvisada na rua bloqueou a passagem do caminhão até o fim do parabéns', 'Verificar bloqueios locais e planejar desvios seguros.'),
    ('O motorista confundiu a caixa de ferramentas com a caixa do almoço e precisou voltar à garagem', 'Aplicar uma lista de conferência antes da saída do veículo.'),
    ('Uma cabra decidiu acompanhar o caminhão e a equipe aguardou até que ela voltasse em segurança para o sítio', 'Comunicar obstáculos e priorizar a segurança na rota.'),
)
FIXED = {'PP1003':0,'PP1006':1,'PP1093':2,'PP1094':3,'PP1099':4,'PP1100':5}

def install(store):
    """Aplica uma vez; não sobrescreve motivos que o gestor já tenha editado."""
    from core import now
    with store.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        c.execute('CREATE TABLE IF NOT EXISTS demo_settings(name TEXT PRIMARY KEY, value TEXT)')
        if c.execute("SELECT 1 FROM demo_settings WHERE name='fun_delays_v1'").fetchone():return
        for code,idx in FIXED.items():
            row=c.execute('SELECT status,reason FROM cargo WHERE code=?',(code,)).fetchone()
            if not row or row['status']!='Atrasada' or row['reason'] not in ('Manutenção do veículo','Interdição na rota','Falha operacional','Condições climáticas'):continue
            reason=SCENARIOS[idx][0];ts=now()
            c.execute('UPDATE cargo SET reason=?,updated=? WHERE code=?',(reason,ts,code))
            c.execute('INSERT INTO history VALUES(?,?,?)',(code,'Atualização do motivo de atraso (cenário fictício): '+reason,ts))
        c.execute("INSERT INTO demo_settings VALUES('fun_delays_v1','1')")
