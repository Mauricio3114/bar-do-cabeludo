from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file
)

from flask_login import (
    login_required,
    current_user
)

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)

from app import db

from app.models.pedido import Pedido
from app.models.item_pedido import ItemPedido
from app.models.produto import Produto
from app.models.usuario import Usuario


caixa_bp = Blueprint(
    "caixa",
    __name__,
    url_prefix="/caixa"
)


# =========================================================
# PROTEÇÃO ADMIN
# =========================================================

def somente_admin():

    if current_user.perfil != "admin":

        flash(
            "Acesso permitido somente ao administrador.",
            "danger"
        )

        return False

    return True


# =========================================================
# CAIXA / VENDAS
# =========================================================

@caixa_bp.route("/")
@login_required
def listar():

    if not somente_admin():
        return redirect(
            url_for("mesas.listar")
        )

    # -----------------------------------------------------
    # DATA SELECIONADA
    # -----------------------------------------------------

    data_str = request.args.get(
        "data",
        ""
    ).strip()

    if data_str:

        try:

            data_selecionada = datetime.strptime(
                data_str,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            data_selecionada = datetime.now().date()

    else:

        data_selecionada = datetime.now().date()


    # -----------------------------------------------------
    # IMPORTANTE:
    # banco está trabalhando em UTC
    #
    # Fortaleza = UTC -3
    #
    # 00:00 Fortaleza = 03:00 UTC
    # -----------------------------------------------------

    inicio_local = datetime.combine(
        data_selecionada,
        datetime.min.time()
    )

    fim_local = (
        inicio_local
        + timedelta(days=1)
    )

    inicio_utc = (
        inicio_local
        + timedelta(hours=3)
    )

    fim_utc = (
        fim_local
        + timedelta(hours=3)
    )


    # -----------------------------------------------------
    # PEDIDOS FINALIZADOS
    # -----------------------------------------------------

    pedidos = (
        Pedido.query
        .filter(
            Pedido.status == "finalizado",
            Pedido.finalizado_em.isnot(None),
            Pedido.finalizado_em >= inicio_utc,
            Pedido.finalizado_em < fim_utc
        )
        .order_by(
            Pedido.finalizado_em.desc()
        )
        .all()
    )


    # -----------------------------------------------------
    # KPIs
    # -----------------------------------------------------

    total_vendido = sum(
        (
            pedido.total or Decimal("0.00")
            for pedido in pedidos
        ),
        Decimal("0.00")
    )

    quantidade = len(
        pedidos
    )

    if quantidade:

        ticket_medio = (
            total_vendido
            / quantidade
        )

    else:

        ticket_medio = Decimal(
            "0.00"
        )


    # -----------------------------------------------------
    # FORMAS DE PAGAMENTO
    # -----------------------------------------------------

    pagamentos = {
        "dinheiro": Decimal("0.00"),
        "pix": Decimal("0.00"),
        "debito": Decimal("0.00"),
        "credito": Decimal("0.00")
    }

    for pedido in pedidos:

        forma = (
            pedido.forma_pagamento
            or ""
        ).strip().lower()

        if forma in pagamentos:

            pagamentos[forma] += (
                pedido.total
                or Decimal("0.00")
            )


    # -----------------------------------------------------
    # MESA X MARMITEX
    # -----------------------------------------------------

    mesas = sum(
        1
        for pedido in pedidos
        if pedido.tipo_atendimento == "mesa"
    )

    marmitex = sum(
        1
        for pedido in pedidos
        if pedido.tipo_atendimento == "marmitex"
    )


    # -----------------------------------------------------
    # HORÁRIO LOCAL PARA EXIBIÇÃO
    # -----------------------------------------------------

    for pedido in pedidos:

        if pedido.finalizado_em:

            pedido.finalizado_local = (
                pedido.finalizado_em
                - timedelta(hours=3)
            )

        else:

            pedido.finalizado_local = None


    return render_template(
        "caixa/listar.html",

        pedidos=pedidos,

        data_selecionada=data_selecionada,

        total_vendido=total_vendido,
        quantidade=quantidade,
        ticket_medio=ticket_medio,

        pagamentos=pagamentos,

        mesas=mesas,
        marmitex=marmitex
    )


# =========================================================
# DETALHE DA VENDA
# =========================================================

@caixa_bp.route("/pedido/<int:pedido_id>")
@login_required
def detalhe_pedido(pedido_id):

    if not somente_admin():
        return redirect(
            url_for("mesas.listar")
        )

    pedido = Pedido.query.get_or_404(
        pedido_id
    )

    # -----------------------------------------------------
    # SOMENTE PEDIDOS FINALIZADOS
    # -----------------------------------------------------

    if pedido.status != "finalizado":

        flash(
            "Este pedido ainda não foi finalizado.",
            "warning"
        )

        return redirect(
            url_for("caixa.listar")
        )

    # -----------------------------------------------------
    # HORÁRIOS LOCAIS - FORTALEZA
    # banco em UTC / Fortaleza UTC-3
    # -----------------------------------------------------

    pedido.criado_local = (
        pedido.criado_em - timedelta(hours=3)
        if pedido.criado_em
        else None
    )

    pedido.finalizado_local = (
        pedido.finalizado_em - timedelta(hours=3)
        if pedido.finalizado_em
        else None
    )

    pedido.fechamento_local = (
        pedido.fechamento_em - timedelta(hours=3)
        if pedido.fechamento_em
        else None
    )

    return render_template(
        "caixa/detalhe.html",
        pedido=pedido
    )


# =========================================================
# FECHAMENTO DO CAIXA
# =========================================================

@caixa_bp.route("/fechamento")
@login_required
def fechamento():

    if not somente_admin():
        return redirect(
            url_for("mesas.listar")
        )

    data_str = request.args.get(
        "data",
        ""
    ).strip()

    if data_str:

        try:
            data_selecionada = datetime.strptime(
                data_str,
                "%Y-%m-%d"
            ).date()

        except ValueError:
            data_selecionada = datetime.now().date()

    else:
        data_selecionada = datetime.now().date()


    # =====================================================
    # PERÍODO LOCAL -> UTC
    # =====================================================

    inicio_local = datetime.combine(
        data_selecionada,
        datetime.min.time()
    )

    fim_local = (
        inicio_local
        + timedelta(days=1)
    )

    inicio_utc = (
        inicio_local
        + timedelta(hours=3)
    )

    fim_utc = (
        fim_local
        + timedelta(hours=3)
    )


    # =====================================================
    # VENDAS FINALIZADAS
    # =====================================================

    pedidos = (
        Pedido.query
        .filter(
            Pedido.status == "finalizado",
            Pedido.finalizado_em.isnot(None),
            Pedido.finalizado_em >= inicio_utc,
            Pedido.finalizado_em < fim_utc
        )
        .order_by(
            Pedido.finalizado_em.asc()
        )
        .all()
    )


    # =====================================================
    # TOTAL
    # =====================================================

    total_vendido = sum(
        (
            pedido.total or Decimal("0.00")
            for pedido in pedidos
        ),
        Decimal("0.00")
    )

    quantidade = len(pedidos)


    # =====================================================
    # MESAS / MARMITEX
    # =====================================================

    mesas = sum(
        1
        for pedido in pedidos
        if pedido.tipo_atendimento == "mesa"
    )

    marmitex = sum(
        1
        for pedido in pedidos
        if pedido.tipo_atendimento == "marmitex"
    )


    # =====================================================
    # FORMAS DE PAGAMENTO
    # =====================================================

    pagamentos = {
        "dinheiro": Decimal("0.00"),
        "pix": Decimal("0.00"),
        "debito": Decimal("0.00"),
        "credito": Decimal("0.00")
    }

    for pedido in pedidos:

        forma = (
            pedido.forma_pagamento
            or ""
        ).strip().lower()

        if forma in pagamentos:

            pagamentos[forma] += (
                pedido.total
                or Decimal("0.00")
            )


    return render_template(
        "caixa/fechamento.html",

        data_selecionada=data_selecionada,

        total_vendido=total_vendido,
        quantidade=quantidade,

        mesas=mesas,
        marmitex=marmitex,

        pagamentos=pagamentos
    )


# =========================================================
# RELATÓRIOS
# =========================================================

@caixa_bp.route("/relatorios")
@login_required
def relatorios():

    if not somente_admin():
        return redirect(
            url_for("mesas.listar")
        )

    # =====================================================
    # FILTROS
    # =====================================================

    hoje = datetime.now().date()

    data_inicial_str = request.args.get(
        "data_inicial",
        hoje.strftime("%Y-%m-%d")
    )

    data_final_str = request.args.get(
        "data_final",
        hoje.strftime("%Y-%m-%d")
    )

    usuario_id = request.args.get(
        "usuario_id",
        ""
    ).strip()

    forma_pagamento = request.args.get(
        "forma_pagamento",
        ""
    ).strip().lower()


    # =====================================================
    # DATAS
    # =====================================================

    try:

        data_inicial = datetime.strptime(
            data_inicial_str,
            "%Y-%m-%d"
        ).date()

    except ValueError:

        data_inicial = hoje


    try:

        data_final = datetime.strptime(
            data_final_str,
            "%Y-%m-%d"
        ).date()

    except ValueError:

        data_final = hoje


    if data_final < data_inicial:
        data_final = data_inicial


    # =====================================================
    # FORTALEZA -> UTC
    # =====================================================

    inicio_local = datetime.combine(
        data_inicial,
        datetime.min.time()
    )

    fim_local = datetime.combine(
        data_final + timedelta(days=1),
        datetime.min.time()
    )

    inicio_utc = (
        inicio_local
        + timedelta(hours=3)
    )

    fim_utc = (
        fim_local
        + timedelta(hours=3)
    )


    # =====================================================
    # CONSULTA DOS PEDIDOS
    # =====================================================

    query = (
        Pedido.query
        .filter(
            Pedido.status == "finalizado",
            Pedido.finalizado_em.isnot(None),
            Pedido.finalizado_em >= inicio_utc,
            Pedido.finalizado_em < fim_utc
        )
    )


    # =====================================================
    # FILTRO GARÇOM
    # =====================================================

    if usuario_id:

        try:

            usuario_id_int = int(
                usuario_id
            )

            query = query.filter(
                Pedido.usuario_id == usuario_id_int
            )

        except ValueError:

            usuario_id = ""


    # =====================================================
    # FILTRO FORMA DE PAGAMENTO
    # =====================================================

    formas_validas = [
        "dinheiro",
        "pix",
        "debito",
        "credito"
    ]

    if forma_pagamento in formas_validas:

        query = query.filter(
            Pedido.forma_pagamento == forma_pagamento
        )

    else:

        forma_pagamento = ""


    pedidos = (
        query
        .order_by(
            Pedido.finalizado_em.desc()
        )
        .all()
    )


    # =====================================================
    # IDS DOS PEDIDOS FILTRADOS
    # =====================================================

    pedido_ids = [
        pedido.id
        for pedido in pedidos
    ]


    # =====================================================
    # KPIs
    # =====================================================

    total_vendido = sum(
        (
            pedido.total or Decimal("0.00")
            for pedido in pedidos
        ),
        Decimal("0.00")
    )

    quantidade_pedidos = len(
        pedidos
    )

    quantidade_mesas = sum(
        1
        for pedido in pedidos
        if pedido.tipo_atendimento == "mesa"
    )

    quantidade_marmitex = sum(
        1
        for pedido in pedidos
        if pedido.tipo_atendimento == "marmitex"
    )


    # =====================================================
    # FORMAS DE PAGAMENTO
    # =====================================================

    totais_pagamento = {
        "dinheiro": Decimal("0.00"),
        "pix": Decimal("0.00"),
        "debito": Decimal("0.00"),
        "credito": Decimal("0.00")
    }

    for pedido in pedidos:

        forma = (
            pedido.forma_pagamento
            or ""
        ).strip().lower()

        if forma in totais_pagamento:

            totais_pagamento[forma] += (
                pedido.total
                or Decimal("0.00")
            )


    # =====================================================
    # PRODUTOS VENDIDOS
    # =====================================================

    produtos_vendidos = []

    if pedido_ids:

        resultado_produtos = (
            db.session.query(
                Produto.id,
                Produto.nome,
                ItemPedido.tipo_item,
                db.func.sum(
                    ItemPedido.quantidade
                ).label("quantidade"),
                db.func.sum(
                    ItemPedido.valor_total
                ).label("total")
            )
            .join(
                ItemPedido,
                ItemPedido.produto_id == Produto.id
            )
            .filter(
                ItemPedido.pedido_id.in_(
                    pedido_ids
                )
            )
            .group_by(
                Produto.id,
                Produto.nome,
                ItemPedido.tipo_item
            )
            .order_by(
                db.func.sum(
                    ItemPedido.quantidade
                ).desc(),
                Produto.nome.asc()
            )
            .all()
        )

        produtos_vendidos = (
            resultado_produtos
        )


    # =====================================================
    # VENDAS POR GARÇOM
    # =====================================================

    vendas_garcom = {}

    for pedido in pedidos:

        nome = (
            pedido.usuario.nome
            if pedido.usuario
            else "Sem usuário"
        )

        if nome not in vendas_garcom:

            vendas_garcom[nome] = {
                "quantidade": 0,
                "total": Decimal("0.00")
            }

        vendas_garcom[nome]["quantidade"] += 1

        vendas_garcom[nome]["total"] += (
            pedido.total
            or Decimal("0.00")
        )


    # =====================================================
    # HORÁRIO LOCAL PARA LISTAGEM
    # =====================================================

    for pedido in pedidos:

        if pedido.finalizado_em:

            pedido.finalizado_local = (
                pedido.finalizado_em
                - timedelta(hours=3)
            )

        else:

            pedido.finalizado_local = None


    # =====================================================
    # USUÁRIOS PARA FILTRO
    # =====================================================

    usuarios = (
        Usuario.query
        .filter_by(
            ativo=True
        )
        .order_by(
            Usuario.nome.asc()
        )
        .all()
    )


    return render_template(
        "caixa/relatorios.html",

        pedidos=pedidos,
        usuarios=usuarios,

        data_inicial=data_inicial,
        data_final=data_final,

        usuario_id=usuario_id,
        forma_pagamento=forma_pagamento,

        total_vendido=total_vendido,
        quantidade_pedidos=quantidade_pedidos,
        quantidade_mesas=quantidade_mesas,
        quantidade_marmitex=quantidade_marmitex,

        totais_pagamento=totais_pagamento,

        produtos_vendidos=produtos_vendidos,
        vendas_garcom=vendas_garcom
    )


# =========================================================
# PDF DOS RELATÓRIOS
# =========================================================

@caixa_bp.route("/relatorios/pdf")
@login_required
def relatorios_pdf():

    if not somente_admin():
        return redirect(
            url_for("mesas.listar")
        )

    # =====================================================
    # FILTROS
    # =====================================================

    hoje = datetime.now().date()

    data_inicial_str = request.args.get(
        "data_inicial",
        hoje.strftime("%Y-%m-%d")
    )

    data_final_str = request.args.get(
        "data_final",
        hoje.strftime("%Y-%m-%d")
    )

    usuario_id = request.args.get(
        "usuario_id",
        ""
    ).strip()

    forma_pagamento = request.args.get(
        "forma_pagamento",
        ""
    ).strip().lower()


    try:

        data_inicial = datetime.strptime(
            data_inicial_str,
            "%Y-%m-%d"
        ).date()

    except ValueError:

        data_inicial = hoje


    try:

        data_final = datetime.strptime(
            data_final_str,
            "%Y-%m-%d"
        ).date()

    except ValueError:

        data_final = hoje


    if data_final < data_inicial:
        data_final = data_inicial


    # =====================================================
    # PERÍODO LOCAL -> UTC
    # =====================================================

    inicio_local = datetime.combine(
        data_inicial,
        datetime.min.time()
    )

    fim_local = datetime.combine(
        data_final + timedelta(days=1),
        datetime.min.time()
    )

    inicio_utc = (
        inicio_local
        + timedelta(hours=3)
    )

    fim_utc = (
        fim_local
        + timedelta(hours=3)
    )


    # =====================================================
    # PEDIDOS
    # =====================================================

    query = (
        Pedido.query
        .filter(
            Pedido.status == "finalizado",
            Pedido.finalizado_em.isnot(None),
            Pedido.finalizado_em >= inicio_utc,
            Pedido.finalizado_em < fim_utc
        )
    )


    usuario_selecionado = None

    if usuario_id:

        try:

            usuario_id_int = int(
                usuario_id
            )

            query = query.filter(
                Pedido.usuario_id == usuario_id_int
            )

            usuario_selecionado = db.session.get(
                Usuario,
                usuario_id_int
            )

        except ValueError:

            usuario_id = ""


    formas_validas = [
        "dinheiro",
        "pix",
        "debito",
        "credito"
    ]

    if forma_pagamento in formas_validas:

        query = query.filter(
            Pedido.forma_pagamento == forma_pagamento
        )

    else:

        forma_pagamento = ""


    pedidos = (
        query
        .order_by(
            Pedido.finalizado_em.asc()
        )
        .all()
    )


    pedido_ids = [
        pedido.id
        for pedido in pedidos
    ]


    # =====================================================
    # RESUMO
    # =====================================================

    total_vendido = sum(
        (
            pedido.total or Decimal("0.00")
            for pedido in pedidos
        ),
        Decimal("0.00")
    )

    quantidade_pedidos = len(
        pedidos
    )

    quantidade_mesas = sum(
        1
        for pedido in pedidos
        if pedido.tipo_atendimento == "mesa"
    )

    quantidade_marmitex = sum(
        1
        for pedido in pedidos
        if pedido.tipo_atendimento == "marmitex"
    )


    pagamentos = {
        "dinheiro": Decimal("0.00"),
        "pix": Decimal("0.00"),
        "debito": Decimal("0.00"),
        "credito": Decimal("0.00")
    }

    for pedido in pedidos:

        forma = (
            pedido.forma_pagamento
            or ""
        ).strip().lower()

        if forma in pagamentos:

            pagamentos[forma] += (
                pedido.total
                or Decimal("0.00")
            )


    # =====================================================
    # PRODUTOS
    # =====================================================

    produtos_vendidos = []

    if pedido_ids:

        produtos_vendidos = (
            db.session.query(
                Produto.nome,
                ItemPedido.tipo_item,
                db.func.sum(
                    ItemPedido.quantidade
                ).label("quantidade"),
                db.func.sum(
                    ItemPedido.valor_total
                ).label("total")
            )
            .join(
                ItemPedido,
                ItemPedido.produto_id == Produto.id
            )
            .filter(
                ItemPedido.pedido_id.in_(
                    pedido_ids
                )
            )
            .group_by(
                Produto.id,
                Produto.nome,
                ItemPedido.tipo_item
            )
            .order_by(
                db.func.sum(
                    ItemPedido.quantidade
                ).desc(),
                Produto.nome.asc()
            )
            .all()
        )


    # =====================================================
    # GARÇONS
    # =====================================================

    vendas_garcom = {}

    for pedido in pedidos:

        nome = (
            pedido.usuario.nome
            if pedido.usuario
            else "Sem usuário"
        )

        if nome not in vendas_garcom:

            vendas_garcom[nome] = {
                "quantidade": 0,
                "total": Decimal("0.00")
            }

        vendas_garcom[nome]["quantidade"] += 1

        vendas_garcom[nome]["total"] += (
            pedido.total
            or Decimal("0.00")
        )


    # =====================================================
    # FUNÇÕES AUXILIARES
    # =====================================================

    def moeda(valor):

        valor = valor or Decimal("0.00")

        return (
            "R$ "
            + "{:,.2f}".format(valor)
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )


    def nome_pagamento(forma):

        nomes = {
            "dinheiro": "Dinheiro",
            "pix": "PIX",
            "debito": "Débito",
            "credito": "Crédito"
        }

        return nomes.get(
            forma,
            forma or "-"
        )


    # =====================================================
    # PDF
    # =====================================================

    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
        title="Relatório - Bar do Cabeludo"
    )


    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle(
        "TituloCabeludo",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=23,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#171717"),
        spaceAfter=4
    )

    subtitulo_style = ParagraphStyle(
        "SubtituloCabeludo",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#666666"),
        spaceAfter=12
    )

    secao_style = ParagraphStyle(
        "SecaoCabeludo",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#c9151e"),
        spaceBefore=10,
        spaceAfter=6
    )


    elementos = []


    # =====================================================
    # CABEÇALHO
    # =====================================================

    elementos.append(
        Paragraph(
            "BAR DO CABELUDO",
            titulo_style
        )
    )

    elementos.append(
        Paragraph(
            "RELATÓRIO GERENCIAL DE VENDAS",
            subtitulo_style
        )
    )


    periodo_texto = (
        f"Período: "
        f"{data_inicial.strftime('%d/%m/%Y')} "
        f"a "
        f"{data_final.strftime('%d/%m/%Y')}"
    )

    if usuario_selecionado:

        periodo_texto += (
            f" | Garçom: "
            f"{usuario_selecionado.nome}"
        )

    if forma_pagamento:

        periodo_texto += (
            f" | Pagamento: "
            f"{nome_pagamento(forma_pagamento)}"
        )


    elementos.append(
        Paragraph(
            periodo_texto,
            subtitulo_style
        )
    )


    # =====================================================
    # RESUMO FINANCEIRO
    # =====================================================

    elementos.append(
        Paragraph(
            "RESUMO",
            secao_style
        )
    )


    dados_resumo = [
        [
            "TOTAL VENDIDO",
            "PEDIDOS",
            "MESAS",
            "MARMITEX"
        ],
        [
            moeda(total_vendido),
            str(quantidade_pedidos),
            str(quantidade_mesas),
            str(quantidade_marmitex)
        ]
    ]


    tabela_resumo = Table(
        dados_resumo,
        colWidths=[
            7 * cm,
            5.5 * cm,
            5.5 * cm,
            5.5 * cm
        ]
    )


    tabela_resumo.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#171717")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "FONTNAME",
                (0, 1),
                (-1, 1),
                "Helvetica-Bold"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                9
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                .4,
                colors.HexColor("#cccccc")
            ),
            (
                "BACKGROUND",
                (0, 1),
                (-1, 1),
                colors.HexColor("#f7f7f7")
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                7
            )
        ])
    )

    elementos.append(
        tabela_resumo
    )

    elementos.append(
        Spacer(
            1,
            0.25 * cm
        )
    )


    # =====================================================
    # PAGAMENTOS
    # =====================================================

    dados_pagamentos = [
        [
            "DINHEIRO",
            "PIX",
            "DÉBITO",
            "CRÉDITO"
        ],
        [
            moeda(pagamentos["dinheiro"]),
            moeda(pagamentos["pix"]),
            moeda(pagamentos["debito"]),
            moeda(pagamentos["credito"])
        ]
    ]


    tabela_pagamentos = Table(
        dados_pagamentos,
        colWidths=[
            5.9 * cm,
            5.9 * cm,
            5.9 * cm,
            5.9 * cm
        ]
    )


    tabela_pagamentos.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#c9151e")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, -1),
                "Helvetica-Bold"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                .4,
                colors.HexColor("#cccccc")
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            )
        ])
    )

    elementos.append(
        tabela_pagamentos
    )


    # =====================================================
    # PRODUTOS VENDIDOS
    # =====================================================

    elementos.append(
        Paragraph(
            "PRODUTOS VENDIDOS",
            secao_style
        )
    )


    dados_produtos = [
        [
            "Produto",
            "Tipo",
            "Quantidade",
            "Total"
        ]
    ]


    for produto in produtos_vendidos:

        tipo = (
            "Adicional"
            if produto.tipo_item == "adicional"
            else "Normal"
        )

        dados_produtos.append([
            produto.nome,
            tipo,
            str(produto.quantidade),
            moeda(produto.total)
        ])


    if len(dados_produtos) == 1:

        dados_produtos.append([
            "Nenhum produto vendido",
            "-",
            "0",
            moeda(Decimal("0.00"))
        ])


    tabela_produtos = Table(
        dados_produtos,
        repeatRows=1,
        colWidths=[
            10 * cm,
            4.5 * cm,
            4 * cm,
            5 * cm
        ]
    )


    tabela_produtos.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#171717")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                .35,
                colors.HexColor("#dddddd")
            ),
            (
                "ALIGN",
                (2, 1),
                (-1, -1),
                "RIGHT"
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#f8f8f8")
                ]
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            )
        ])
    )

    elementos.append(
        tabela_produtos
    )


    # =====================================================
    # VENDAS POR GARÇOM
    # =====================================================

    elementos.append(
        Paragraph(
            "VENDAS POR GARÇOM",
            secao_style
        )
    )


    dados_garcom = [
        [
            "Garçom",
            "Pedidos",
            "Total"
        ]
    ]


    for nome, dados in vendas_garcom.items():

        dados_garcom.append([
            nome,
            str(dados["quantidade"]),
            moeda(dados["total"])
        ])


    if len(dados_garcom) == 1:

        dados_garcom.append([
            "Nenhuma venda",
            "0",
            moeda(Decimal("0.00"))
        ])


    tabela_garcom = Table(
        dados_garcom,
        repeatRows=1,
        colWidths=[
            13 * cm,
            5 * cm,
            5.5 * cm
        ]
    )


    tabela_garcom.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#c9151e")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                .35,
                colors.HexColor("#dddddd")
            ),
            (
                "ALIGN",
                (1, 1),
                (-1, -1),
                "RIGHT"
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#f8f8f8")
                ]
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            )
        ])
    )

    elementos.append(
        tabela_garcom
    )


    # =====================================================
    # VENDAS DO PERÍODO
    # =====================================================

    elementos.append(
        PageBreak()
    )

    elementos.append(
        Paragraph(
            "VENDAS DO PERÍODO",
            secao_style
        )
    )


    dados_vendas = [
        [
            "Pedido",
            "Atendimento",
            "Garçom",
            "Pagamento",
            "Data/Hora",
            "Total"
        ]
    ]


    for pedido in pedidos:

        if pedido.tipo_atendimento == "marmitex":

            atendimento = (
                f"Marmitex "
                f"#{pedido.numero_marmitex or '-'}"
            )

        else:

            atendimento = (
                f"Mesa "
                f"{pedido.mesa.numero:02d}"
                if pedido.mesa
                else "Mesa"
            )


        horario = (
            pedido.finalizado_em
            - timedelta(hours=3)
        )


        dados_vendas.append([
            f"#{pedido.id}",
            atendimento,
            (
                pedido.usuario.nome
                if pedido.usuario
                else "-"
            ),
            nome_pagamento(
                pedido.forma_pagamento
            ),
            horario.strftime(
                "%d/%m/%Y %H:%M"
            ),
            moeda(
                pedido.total
            )
        ])


    if len(dados_vendas) == 1:

        dados_vendas.append([
            "-",
            "Nenhuma venda",
            "-",
            "-",
            "-",
            moeda(Decimal("0.00"))
        ])


    tabela_vendas = Table(
        dados_vendas,
        repeatRows=1,
        colWidths=[
            2.2 * cm,
            4.2 * cm,
            5.4 * cm,
            4 * cm,
            4.5 * cm,
            3.5 * cm
        ]
    )


    tabela_vendas.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#171717")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                7.5
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                .35,
                colors.HexColor("#dddddd")
            ),
            (
                "ALIGN",
                (-1, 1),
                (-1, -1),
                "RIGHT"
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#f8f8f8")
                ]
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5
            )
        ])
    )

    elementos.append(
        tabela_vendas
    )


    # =====================================================
    # GERAÇÃO
    # =====================================================

    documento.build(
        elementos
    )

    buffer.seek(0)


    nome_arquivo = (
        "relatorio_"
        + data_inicial.strftime("%d-%m-%Y")
        + "_a_"
        + data_final.strftime("%d-%m-%Y")
        + ".pdf"
    )


    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=nome_arquivo
    )


# =========================================================
# PDF DO FECHAMENTO DO DIA
# =========================================================

@caixa_bp.route("/fechamento/pdf")
@login_required
def fechamento_pdf():

    if not somente_admin():
        return redirect(
            url_for("mesas.listar")
        )

    # =====================================================
    # DATA
    # =====================================================

    data_str = request.args.get(
        "data",
        ""
    ).strip()

    if data_str:

        try:

            data_selecionada = datetime.strptime(
                data_str,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            data_selecionada = datetime.now().date()

    else:

        data_selecionada = datetime.now().date()


    # =====================================================
    # PERÍODO LOCAL -> UTC
    # =====================================================

    inicio_local = datetime.combine(
        data_selecionada,
        datetime.min.time()
    )

    fim_local = (
        inicio_local
        + timedelta(days=1)
    )

    inicio_utc = (
        inicio_local
        + timedelta(hours=3)
    )

    fim_utc = (
        fim_local
        + timedelta(hours=3)
    )


    # =====================================================
    # PEDIDOS FINALIZADOS
    # =====================================================

    pedidos = (
        Pedido.query
        .filter(
            Pedido.status == "finalizado",
            Pedido.finalizado_em.isnot(None),
            Pedido.finalizado_em >= inicio_utc,
            Pedido.finalizado_em < fim_utc
        )
        .order_by(
            Pedido.finalizado_em.asc()
        )
        .all()
    )


    # =====================================================
    # TOTAIS
    # =====================================================

    total_vendido = sum(
        (
            pedido.total or Decimal("0.00")
            for pedido in pedidos
        ),
        Decimal("0.00")
    )

    quantidade = len(
        pedidos
    )

    mesas = sum(
        1
        for pedido in pedidos
        if pedido.tipo_atendimento == "mesa"
    )

    marmitex = sum(
        1
        for pedido in pedidos
        if pedido.tipo_atendimento == "marmitex"
    )


    # =====================================================
    # FORMAS DE PAGAMENTO
    # =====================================================

    pagamentos = {
        "dinheiro": Decimal("0.00"),
        "pix": Decimal("0.00"),
        "debito": Decimal("0.00"),
        "credito": Decimal("0.00")
    }

    for pedido in pedidos:

        forma = (
            pedido.forma_pagamento
            or ""
        ).strip().lower()

        if forma in pagamentos:

            pagamentos[forma] += (
                pedido.total
                or Decimal("0.00")
            )


    # =====================================================
    # FUNÇÕES AUXILIARES
    # =====================================================

    def moeda(valor):

        valor = (
            valor
            or Decimal("0.00")
        )

        return (
            "R$ "
            + "{:,.2f}".format(valor)
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )


    def nome_pagamento(forma):

        nomes = {
            "dinheiro": "Dinheiro",
            "pix": "PIX",
            "debito": "Débito",
            "credito": "Crédito"
        }

        return nomes.get(
            forma,
            forma or "-"
        )


    # =====================================================
    # CRIA PDF
    # =====================================================

    buffer = BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
        title=(
            "Fechamento do Dia - "
            "Bar do Cabeludo"
        )
    )


    styles = getSampleStyleSheet()


    titulo_style = ParagraphStyle(
        "TituloFechamento",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=23,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#171717"),
        spaceAfter=4
    )


    subtitulo_style = ParagraphStyle(
        "SubtituloFechamento",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#666666"),
        spaceAfter=12
    )


    secao_style = ParagraphStyle(
        "SecaoFechamento",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#c9151e"),
        spaceBefore=10,
        spaceAfter=6
    )


    elementos = []


    # =====================================================
    # CABEÇALHO
    # =====================================================

    elementos.append(
        Paragraph(
            "BAR DO CABELUDO",
            titulo_style
        )
    )


    elementos.append(
        Paragraph(
            "FECHAMENTO DO CAIXA",
            subtitulo_style
        )
    )


    elementos.append(
        Paragraph(
            (
                "Data: "
                + data_selecionada.strftime(
                    "%d/%m/%Y"
                )
            ),
            subtitulo_style
        )
    )


    # =====================================================
    # RESUMO
    # =====================================================

    elementos.append(
        Paragraph(
            "RESUMO DO DIA",
            secao_style
        )
    )


    dados_resumo = [

        [
            "TOTAL DO DIA",
            "PEDIDOS",
            "MESAS",
            "MARMITEX"
        ],

        [
            moeda(total_vendido),
            str(quantidade),
            str(mesas),
            str(marmitex)
        ]

    ]


    tabela_resumo = Table(
        dados_resumo,
        colWidths=[
            7 * cm,
            5.5 * cm,
            5.5 * cm,
            5.5 * cm
        ]
    )


    tabela_resumo.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#171717")
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, -1),
                "Helvetica-Bold"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                9
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                .4,
                colors.HexColor("#cccccc")
            ),

            (
                "BACKGROUND",
                (0, 1),
                (-1, 1),
                colors.HexColor("#f7f7f7")
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                8
            )

        ])
    )


    elementos.append(
        tabela_resumo
    )


    elementos.append(
        Spacer(
            1,
            0.3 * cm
        )
    )


    # =====================================================
    # FORMAS DE PAGAMENTO
    # =====================================================

    elementos.append(
        Paragraph(
            "RECEBIMENTOS",
            secao_style
        )
    )


    dados_pagamentos = [

        [
            "DINHEIRO",
            "PIX",
            "DÉBITO",
            "CRÉDITO"
        ],

        [
            moeda(
                pagamentos["dinheiro"]
            ),

            moeda(
                pagamentos["pix"]
            ),

            moeda(
                pagamentos["debito"]
            ),

            moeda(
                pagamentos["credito"]
            )
        ]

    ]


    tabela_pagamentos = Table(
        dados_pagamentos,
        colWidths=[
            5.9 * cm,
            5.9 * cm,
            5.9 * cm,
            5.9 * cm
        ]
    )


    tabela_pagamentos.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#c9151e")
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, -1),
                "Helvetica-Bold"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                .4,
                colors.HexColor("#cccccc")
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                7
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                7
            )

        ])
    )


    elementos.append(
        tabela_pagamentos
    )


    # =====================================================
    # VENDAS DO DIA
    # =====================================================

    elementos.append(
        Paragraph(
            "VENDAS DO DIA",
            secao_style
        )
    )


    dados_vendas = [

        [
            "Pedido",
            "Atendimento",
            "Garçom",
            "Pagamento",
            "Hora",
            "Total"
        ]

    ]


    for pedido in pedidos:

        # ---------------------------------------------
        # Atendimento
        # ---------------------------------------------

        if pedido.tipo_atendimento == "marmitex":

            atendimento = (
                "Marmitex #"
                + str(
                    pedido.numero_marmitex
                    or "-"
                )
            )

        else:

            if pedido.mesa:

                atendimento = (
                    "Mesa "
                    + f"{pedido.mesa.numero:02d}"
                )

            else:

                atendimento = "Mesa"


        # ---------------------------------------------
        # Hora local
        # ---------------------------------------------

        horario_local = (
            pedido.finalizado_em
            - timedelta(hours=3)
        )


        # ---------------------------------------------
        # Linha
        # ---------------------------------------------

        dados_vendas.append([

            f"#{pedido.id}",

            atendimento,

            (
                pedido.usuario.nome
                if pedido.usuario
                else "-"
            ),

            nome_pagamento(
                pedido.forma_pagamento
            ),

            horario_local.strftime(
                "%H:%M"
            ),

            moeda(
                pedido.total
            )

        ])


    if len(dados_vendas) == 1:

        dados_vendas.append([

            "-",

            "Nenhuma venda",

            "-",

            "-",

            "-",

            moeda(
                Decimal("0.00")
            )

        ])


    tabela_vendas = Table(
        dados_vendas,
        repeatRows=1,
        colWidths=[
            2.3 * cm,
            5 * cm,
            6 * cm,
            4.2 * cm,
            3 * cm,
            3.5 * cm
        ]
    )


    tabela_vendas.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#171717")
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                .35,
                colors.HexColor("#dddddd")
            ),

            (
                "ALIGN",
                (-1, 1),
                (-1, -1),
                "RIGHT"
            ),

            (
                "ALIGN",
                (4, 1),
                (4, -1),
                "CENTER"
            ),

            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#f8f8f8")
                ]
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            )

        ])
    )


    elementos.append(
        tabela_vendas
    )


    # =====================================================
    # RODAPÉ
    # =====================================================

    elementos.append(
        Spacer(
            1,
            0.5 * cm
        )
    )


    elementos.append(
        Paragraph(
            (
                "Bar do Cabeludo • "
                "Fechamento diário do caixa"
            ),
            subtitulo_style
        )
    )


    # =====================================================
    # GERA PDF
    # =====================================================

    documento.build(
        elementos
    )

    buffer.seek(0)


    nome_arquivo = (
        "fechamento_"
        + data_selecionada.strftime(
            "%d-%m-%Y"
        )
        + ".pdf"
    )


    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=nome_arquivo
    )