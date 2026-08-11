from decimal import Decimal
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)
from flask_login import login_required, current_user

from app import db
from app.models.mesa import Mesa
from app.models.produto import Produto
from app.models.pedido import Pedido
from app.models.item_pedido import ItemPedido
from app.models.item_pedido_acompanhamento import ItemPedidoAcompanhamento

from app.services.impressao import (
    imprimir_cozinha,
    imprimir_destinos_iniciais,
    imprimir_novo_consumo_por_destino
)

from app.services.fila_impressao import (
    enfileirar_pedido_inicial,
    enfileirar_cozinha,
    enfileirar_novo_consumo
)


pedidos_bp = Blueprint(
    "pedidos",
    __name__,
    url_prefix="/pedidos"
)


# =========================================================
# ABRIR / MONTAR PEDIDO DA MESA
# =========================================================

@pedidos_bp.route("/mesa/<int:mesa_id>", methods=["GET", "POST"])
@login_required
def mesa(mesa_id):

    mesa = Mesa.query.get_or_404(mesa_id)

    # -----------------------------------------------------
    # Procura pedido ainda aberto nessa mesa
    # -----------------------------------------------------

    pedido = (
        Pedido.query
        .filter(
            Pedido.mesa_id == mesa.id,
            Pedido.status.notin_(["finalizado", "cancelado"])
        )
        .order_by(Pedido.id.desc())
        .first()
    )

    # =====================================================
    # SE A MESA JÁ POSSUI PEDIDO, ABRE O PEDIDO
    # =====================================================

    if pedido and request.method == "GET":

        return redirect(
            url_for(
                "pedidos.detalhes",
                pedido_id=pedido.id
            )
        )

    # =====================================================
    # PRODUTOS ATIVOS
    # =====================================================

    carnes = (
        Produto.query
        .filter_by(
            ativo=True,
            tipo="carne"
        )
        .order_by(
            Produto.ordem.asc(),
            Produto.nome.asc()
        )
        .all()
    )

    acompanhamentos = (
        Produto.query
        .filter_by(
            ativo=True,
            tipo="acompanhamento"
        )
        .order_by(
            Produto.ordem.asc(),
            Produto.nome.asc()
        )
        .all()
    )

    adicionais = (
        Produto.query
        .filter_by(
            ativo=True,
            permite_adicional=True
        )
        .order_by(
            Produto.ordem.asc(),
            Produto.nome.asc()
        )
        .all()
    )

    bebidas = (
        Produto.query
        .filter_by(
            ativo=True,
            tipo="bebida"
        )
        .order_by(
            Produto.ordem.asc(),
            Produto.nome.asc()
        )
        .all()
    )

    sobremesas = (
        Produto.query
        .filter_by(
            ativo=True,
            tipo="sobremesa"
        )
        .order_by(
            Produto.ordem.asc(),
            Produto.nome.asc()
        )
        .all()
    )

    outros = (
        Produto.query
        .filter_by(
            ativo=True,
            tipo="outro"
        )
        .order_by(
            Produto.ordem.asc(),
            Produto.nome.asc()
        )
        .all()
    )

    # =====================================================
    # SALVAR / ENVIAR PEDIDO
    # =====================================================

    if request.method == "POST":

        # -------------------------------------------------
        # Evita dois pedidos abertos na mesma mesa
        # -------------------------------------------------

        if pedido:

            flash(
                "Esta mesa já possui um pedido em andamento.",
                "warning"
            )

            return redirect(
                url_for(
                    "pedidos.mesa",
                    mesa_id=mesa.id
                )
            )

        # =================================================
        # LÊ OS PRATOS DA NOVA TELA
        #
        # Exemplo:
        #
        # prato_1_carne_id
        # prato_1_acompanhamentos
        #
        # prato_2_carne_id
        # prato_2_acompanhamentos
        # =================================================

        pratos_selecionados = []

        indices_pratos = set()

        for nome_campo in request.form.keys():

            if (
                nome_campo.startswith("prato_")
                and nome_campo.endswith("_carne_id")
            ):

                partes = nome_campo.split("_")

                if len(partes) >= 4:

                    try:

                        indice = int(
                            partes[1]
                        )

                        indices_pratos.add(
                            indice
                        )

                    except (TypeError, ValueError):

                        continue

        # -------------------------------------------------
        # Monta cada prato separadamente
        # -------------------------------------------------

        for indice in sorted(indices_pratos):

            carne_id = request.form.get(
                f"prato_{indice}_carne_id",
                type=int
            )

            if not carne_id:
                continue

            carne = db.session.get(
                Produto,
                carne_id
            )

            if (
                not carne
                or not carne.ativo
                or carne.tipo != "carne"
            ):
                continue

            acompanhamento_ids = request.form.getlist(
                f"prato_{indice}_acompanhamentos"
            )

            acompanhamentos_do_prato = []

            ids_ja_adicionados = set()

            for acompanhamento_id in acompanhamento_ids:

                try:

                    acompanhamento_id = int(
                        acompanhamento_id
                    )

                except (TypeError, ValueError):

                    continue

                # Evita acompanhamento duplicado
                if acompanhamento_id in ids_ja_adicionados:
                    continue

                acompanhamento = db.session.get(
                    Produto,
                    acompanhamento_id
                )

                if (
                    acompanhamento
                    and acompanhamento.ativo
                    and acompanhamento.tipo == "acompanhamento"
                ):

                    acompanhamentos_do_prato.append(
                        acompanhamento
                    )

                    ids_ja_adicionados.add(
                        acompanhamento.id
                    )

            pratos_selecionados.append(
                {
                    "carne": carne,
                    "acompanhamentos": acompanhamentos_do_prato
                }
            )

        # =================================================
        # VERIFICA SE EXISTE OUTRO PRATO SELECIONADO
        # =================================================

        possui_outro_prato = False

        for produto in outros:

            quantidade = request.form.get(
                f"produto_{produto.id}",
                0,
                type=int
            )

            if (
                quantidade
                and quantidade > 0
            ):

                possui_outro_prato = True
                break

        # =================================================
        # VALIDAÇÃO
        # =================================================

        if (
            not pratos_selecionados
            and not possui_outro_prato
        ):

            flash(
                "Selecione pelo menos uma carne ou um prato.",
                "danger"
            )

            return redirect(
                url_for(
                    "pedidos.mesa",
                    mesa_id=mesa.id
                )
            )

        # =================================================
        # CRIA PEDIDO
        # =================================================

        novo_pedido = Pedido(
            tipo_atendimento="mesa",
            mesa_id=mesa.id,
            usuario_id=current_user.id,
            status="cozinha",
            subtotal=Decimal("0.00"),
            desconto=Decimal("0.00"),
            total=Decimal("0.00")
        )

        db.session.add(
            novo_pedido
        )

        db.session.flush()

        total_pedido = Decimal("0.00")

        # =================================================
        # CRIA CADA PRATO INDIVIDUALMENTE
        # =================================================

        for prato in pratos_selecionados:

            carne = prato["carne"]

            acompanhamentos_do_prato = (
                prato["acompanhamentos"]
            )

            if carne.preco is None:
                continue

            valor_unitario = Decimal(
                str(carne.preco)
            )

            # Cada card da tela representa UM prato
            quantidade = 1

            valor_prato = valor_unitario

            item_prato = ItemPedido(
                pedido_id=novo_pedido.id,
                produto_id=carne.id,
                tipo_item="normal",
                quantidade=quantidade,
                valor_unitario=valor_unitario,
                valor_total=valor_prato
            )

            db.session.add(
                item_prato
            )

            # Precisamos do ID do item para vincular
            # os acompanhamentos exclusivamente a ele.
            db.session.flush()

            # =================================================
            # ACOMPANHAMENTOS EXCLUSIVOS DESTE PRATO
            # =================================================

            for acompanhamento in acompanhamentos_do_prato:

                vinculo = ItemPedidoAcompanhamento(
                    item_pedido_id=item_prato.id,
                    produto_id=acompanhamento.id
                )

                db.session.add(
                    vinculo
                )

            total_pedido += valor_prato

        # =================================================
        # ADICIONAIS
        # =================================================

        for adicional in adicionais:

            quantidade = request.form.get(
                f"adicional_{adicional.id}",
                0,
                type=int
            )

            if (
                quantidade is None
                or quantidade <= 0
            ):
                continue

            if adicional.preco_adicional is None:
                continue

            valor_unitario = Decimal(
                str(
                    adicional.preco_adicional
                )
            )

            valor_total_adicional = (
                valor_unitario
                * quantidade
            )

            item_adicional = ItemPedido(
                pedido_id=novo_pedido.id,
                produto_id=adicional.id,
                tipo_item="adicional",
                quantidade=quantidade,
                valor_unitario=valor_unitario,
                valor_total=valor_total_adicional
            )

            db.session.add(
                item_adicional
            )

            total_pedido += (
                valor_total_adicional
            )

        # =================================================
        # BEBIDAS / SOBREMESAS / OUTROS
        # =================================================

        produtos_extras = (
            bebidas
            + sobremesas
            + outros
        )

        for produto in produtos_extras:

            quantidade = request.form.get(
                f"produto_{produto.id}",
                0,
                type=int
            )

            if (
                quantidade is None
                or quantidade <= 0
            ):
                continue

            if produto.preco is None:
                continue

            valor_unitario = Decimal(
                str(
                    produto.preco
                )
            )

            valor_total_item = (
                valor_unitario
                * quantidade
            )

            item = ItemPedido(
                pedido_id=novo_pedido.id,
                produto_id=produto.id,
                tipo_item="normal",
                quantidade=quantidade,
                valor_unitario=valor_unitario,
                valor_total=valor_total_item
            )

            db.session.add(
                item
            )

            total_pedido += (
                valor_total_item
            )

        # =================================================
        # TOTAL
        # =================================================

        novo_pedido.subtotal = total_pedido
        novo_pedido.total = total_pedido

        # Garante que itens e vínculos estejam disponíveis
        # antes de verificar destinos e imprimir.
        db.session.flush()

        # =================================================
        # DESCOBRE DESTINOS DO PEDIDO
        # =================================================

        possui_churrasqueira = any(
            getattr(
                item.produto,
                "destino_preparo",
                "sem_preparo"
            ) == "churrasqueira"
            for item in novo_pedido.itens
        )

        possui_cozinha = any(
            getattr(
                item.produto,
                "destino_preparo",
                "sem_preparo"
            ) == "cozinha"
            for item in novo_pedido.itens
        )

        # =================================================
        # DEFINE FLUXO
        # =================================================

        if possui_churrasqueira:

            novo_pedido.status = "churrasqueira"

            novo_pedido.enviado_churrasqueira_em = (
                datetime.utcnow()
            )

            mesa.status = "churrasqueira"

        elif possui_cozinha:

            novo_pedido.status = "cozinha"

            novo_pedido.enviado_cozinha_em = (
                datetime.utcnow()
            )

            mesa.status = "cozinha"

        else:

            novo_pedido.status = "servido"

            novo_pedido.servido_em = (
                datetime.utcnow()
            )

            mesa.status = "servido"

        # =================================================
        # SALVA
        # =================================================

        db.session.commit()

        # =================================================
        # FILA DE IMPRESSÃO
        # =================================================

        try:

            enfileirar_pedido_inicial(
                novo_pedido
            )

            db.session.commit()

        except Exception as erro:

            db.session.rollback()

            print(
                "ERRO FILA IMPRESSÃO INICIAL:",
                erro
            )

        # =================================================
        # MENSAGEM
        # =================================================

        if (
            possui_churrasqueira
            and possui_cozinha
        ):

            mensagem = (
                f"Pedido da {mesa.nome} enviado "
                "para churrasqueira e cozinha."
            )

        elif possui_churrasqueira:

            mensagem = (
                f"Pedido da {mesa.nome} enviado "
                "para a churrasqueira."
            )

        elif possui_cozinha:

            mensagem = (
                f"Pedido da {mesa.nome} enviado "
                "direto para a cozinha."
            )

        else:

            mensagem = (
                f"Pedido da {mesa.nome} registrado."
            )

        flash(
            mensagem,
            "success"
        )

        return redirect(
            url_for(
                "mesas.listar"
            )
        )

    # =====================================================
    # GET
    # =====================================================

    return render_template(
        "pedidos/mesa.html",
        mesa=mesa,
        pedido=pedido,
        carnes=carnes,
        acompanhamentos=acompanhamentos,
        adicionais=adicionais,
        bebidas=bebidas,
        sobremesas=sobremesas,
        outros=outros
    )


# =========================================================
# VISUALIZAR PEDIDO EM ANDAMENTO
# =========================================================

@pedidos_bp.route("/<int:pedido_id>")
@login_required
def detalhes(pedido_id):

    pedido = Pedido.query.get_or_404(
        pedido_id
    )

    return render_template(
        "pedidos/detalhes.html",
        pedido=pedido
    )


# =========================================================
# CARNE PRONTA / ENVIAR PARA COZINHA
# =========================================================

@pedidos_bp.route(
    "/<int:pedido_id>/carne-pronta",
    methods=["POST"]
)
@login_required
def carne_pronta(pedido_id):

    pedido = Pedido.query.get_or_404(
        pedido_id
    )

    # Só pode executar essa ação
    # enquanto estiver na churrasqueira
    if pedido.status != "churrasqueira":

        flash(
            "Este pedido não está aguardando a churrasqueira.",
            "warning"
        )

        return redirect(
            url_for(
                "pedidos.detalhes",
                pedido_id=pedido.id
            )
        )

    pedido.status = "cozinha"
    pedido.enviado_cozinha_em = datetime.utcnow()

    if pedido.mesa:
        pedido.mesa.status = "cozinha"

    db.session.commit()

    # =====================================================
    # IMPRESSÃO - COZINHA
    # =====================================================

    try:

        enfileirar_cozinha(
            pedido
        )

        db.session.commit()

    except Exception as erro:

        db.session.rollback()

        print(
            "ERRO FILA IMPRESSÃO COZINHA:",
            erro
        )

    flash(
        "Carne liberada. Pedido enviado para a cozinha.",
        "success"
    )

    return redirect(
        url_for(
            "pedidos.detalhes",
            pedido_id=pedido.id
        )
    )


# =========================================================
# ACOMPANHAMENTOS ENTREGUES / PEDIDO SERVIDO
# =========================================================

@pedidos_bp.route(
    "/<int:pedido_id>/servir",
    methods=["POST"]
)
@login_required
def servir(pedido_id):

    pedido = Pedido.query.get_or_404(
        pedido_id
    )

    # Só pode servir se estiver na cozinha
    if pedido.status != "cozinha":

        flash(
            "Este pedido não está aguardando a cozinha.",
            "warning"
        )

        return redirect(
            url_for(
                "pedidos.detalhes",
                pedido_id=pedido.id
            )
        )

    # =====================================================
    # ATUALIZA PEDIDO
    # =====================================================

    pedido.status = "servido"
    pedido.servido_em = datetime.utcnow()

    # =====================================================
    # ATUALIZA MESA
    # =====================================================

    if pedido.mesa:
        pedido.mesa.status = "servido"

    db.session.commit()

    if pedido.tipo_atendimento == "marmitex":

        flash(
            "Marmitex pronto para entrega.",
            "success"
        )

    else:

        flash(
            "Acompanhamentos retirados. Pedido servido à mesa.",
            "success"
        )

    return redirect(
        url_for(
            "pedidos.detalhes",
            pedido_id=pedido.id
        )
    )


# =========================================================
# ADICIONAR NOVO CONSUMO AO PEDIDO
# =========================================================

@pedidos_bp.route(
    "/<int:pedido_id>/adicionar-consumo",
    methods=["GET", "POST"]
)
@login_required
def adicionar_consumo(pedido_id):

    pedido = Pedido.query.get_or_404(
        pedido_id
    )

    # Pedido encerrado não recebe novos itens
    if pedido.status in [
        "finalizado",
        "cancelado",
        "fechamento"
    ]:

        flash(
            "Este pedido não permite novos consumos.",
            "warning"
        )

        return redirect(
            url_for(
                "pedidos.detalhes",
                pedido_id=pedido.id
            )
        )

    # =====================================================
    # PRODUTOS DISPONÍVEIS
    # =====================================================

    adicionais = (
        Produto.query
        .filter_by(
            ativo=True,
            permite_adicional=True
        )
        .order_by(
            Produto.ordem.asc(),
            Produto.nome.asc()
        )
        .all()
    )

    bebidas = (
        Produto.query
        .filter_by(
            ativo=True,
            tipo="bebida"
        )
        .order_by(
            Produto.ordem.asc(),
            Produto.nome.asc()
        )
        .all()
    )

    sobremesas = (
        Produto.query
        .filter_by(
            ativo=True,
            tipo="sobremesa"
        )
        .order_by(
            Produto.ordem.asc(),
            Produto.nome.asc()
        )
        .all()
    )

    outros = (
        Produto.query
        .filter_by(
            ativo=True,
            tipo="outro"
        )
        .order_by(
            Produto.ordem.asc(),
            Produto.nome.asc()
        )
        .all()
    )

    # =====================================================
    # SALVAR NOVO CONSUMO
    # =====================================================

    if request.method == "POST":

        valor_adicionado = Decimal("0.00")
        itens_adicionados = 0
        itens_novos = []

        # =================================================
        # ADICIONAIS
        # =================================================

        for produto in adicionais:

            quantidade = request.form.get(
                f"adicional_{produto.id}",
                0,
                type=int
            )

            if (
                not quantidade
                or quantidade <= 0
            ):
                continue

            if produto.preco_adicional is None:
                continue

            valor_unitario = Decimal(
                str(
                    produto.preco_adicional
                )
            )

            valor_total = (
                valor_unitario
                * quantidade
            )

            item = ItemPedido(
                pedido_id=pedido.id,
                produto_id=produto.id,
                tipo_item="adicional",
                quantidade=quantidade,
                valor_unitario=valor_unitario,
                valor_total=valor_total,
                observacao=(
                    "Adicionado durante o atendimento"
                )
            )

            db.session.add(
                item
            )

            itens_novos.append(
                item
            )

            valor_adicionado += valor_total
            itens_adicionados += quantidade

        # =================================================
        # BEBIDAS / SOBREMESAS / OUTROS
        # =================================================

        produtos_normais = (
            bebidas
            + sobremesas
            + outros
        )

        for produto in produtos_normais:

            quantidade = request.form.get(
                f"produto_{produto.id}",
                0,
                type=int
            )

            if (
                not quantidade
                or quantidade <= 0
            ):
                continue

            if produto.preco is None:
                continue

            valor_unitario = Decimal(
                str(
                    produto.preco
                )
            )

            valor_total = (
                valor_unitario
                * quantidade
            )

            item = ItemPedido(
                pedido_id=pedido.id,
                produto_id=produto.id,
                tipo_item="normal",
                quantidade=quantidade,
                valor_unitario=valor_unitario,
                valor_total=valor_total,
                observacao=(
                    "Adicionado durante o atendimento"
                )
            )

            db.session.add(
                item
            )

            itens_novos.append(
                item
            )

            valor_adicionado += valor_total
            itens_adicionados += quantidade

        # =================================================
        # VALIDAÇÃO
        # =================================================

        if itens_adicionados == 0:

            flash(
                "Selecione pelo menos um item.",
                "warning"
            )

            return redirect(
                url_for(
                    "pedidos.adicionar_consumo",
                    pedido_id=pedido.id
                )
            )

        # =================================================
        # TOTAL
        # =================================================

        pedido.subtotal = (
            Decimal(
                str(
                    pedido.subtotal or 0
                )
            )
            + valor_adicionado
        )

        pedido.total = (
            Decimal(
                str(
                    pedido.total or 0
                )
            )
            + valor_adicionado
        )

        db.session.flush()

        db.session.commit()

        # =================================================
        # IMPRESSÃO DO NOVO CONSUMO POR DESTINO
        # =================================================

        try:

            enfileirar_novo_consumo(
                pedido,
                itens_novos
            )

            db.session.commit()

        except Exception as erro:

            db.session.rollback()

            print(
                "ERRO FILA IMPRESSÃO NOVO CONSUMO:",
                erro
            )

        flash(
            "Novo consumo adicionado ao pedido.",
            "success"
        )

        return redirect(
            url_for(
                "pedidos.detalhes",
                pedido_id=pedido.id
            )
        )

    return render_template(
        "pedidos/adicionar_consumo.html",
        pedido=pedido,
        adicionais=adicionais,
        bebidas=bebidas,
        sobremesas=sobremesas,
        outros=outros
    )


# =========================================================
# PEDIR CONTA / ENVIAR PARA FECHAMENTO
# =========================================================

@pedidos_bp.route(
    "/<int:pedido_id>/fechamento",
    methods=["POST"]
)
@login_required
def iniciar_fechamento(pedido_id):

    pedido = Pedido.query.get_or_404(
        pedido_id
    )

    if pedido.status != "servido":

        flash(
            "Somente pedidos servidos podem ir para fechamento.",
            "warning"
        )

        return redirect(
            url_for(
                "pedidos.detalhes",
                pedido_id=pedido.id
            )
        )

    pedido.status = "fechamento"
    pedido.fechamento_em = datetime.utcnow()

    if pedido.mesa:
        pedido.mesa.status = "fechamento"

    db.session.commit()

    flash(
        "Conta enviada para fechamento.",
        "success"
    )

    return redirect(
        url_for(
            "pedidos.detalhes",
            pedido_id=pedido.id
        )
    )


# =========================================================
# CONFIRMAR PAGAMENTO / FINALIZAR PEDIDO
# =========================================================

@pedidos_bp.route(
    "/<int:pedido_id>/finalizar",
    methods=["POST"]
)
@login_required
def finalizar(pedido_id):

    pedido = Pedido.query.get_or_404(
        pedido_id
    )

    if pedido.status != "fechamento":

        flash(
            "Este pedido não está em fechamento.",
            "warning"
        )

        return redirect(
            url_for(
                "pedidos.detalhes",
                pedido_id=pedido.id
            )
        )

    forma_pagamento = (
        request.form.get(
            "forma_pagamento",
            ""
        )
        .strip()
        .lower()
    )

    formas_permitidas = [
        "dinheiro",
        "pix",
        "debito",
        "credito"
    ]

    if forma_pagamento not in formas_permitidas:

        flash(
            "Selecione uma forma de pagamento.",
            "warning"
        )

        return redirect(
            url_for(
                "pedidos.detalhes",
                pedido_id=pedido.id
            )
        )

    # =====================================================
    # FINALIZA PEDIDO
    # =====================================================

    pedido.forma_pagamento = forma_pagamento
    pedido.status = "finalizado"
    pedido.finalizado_em = datetime.utcnow()

    # =====================================================
    # LIBERA MESA
    # =====================================================

    if pedido.mesa:
        pedido.mesa.status = "livre"

    db.session.commit()

    flash(
        "Pagamento confirmado. Mesa liberada.",
        "success"
    )

    return redirect(
        url_for("mesas.listar")
    )


# =========================================================
# NOVO PEDIDO MARMITEX
# =========================================================

@pedidos_bp.route(
    "/marmitex/novo",
    methods=["GET", "POST"]
)
@login_required
def novo_marmitex():

    # =====================================================
    # PRODUTOS DISPONÍVEIS
    # =====================================================

    carnes = (
        Produto.query
        .filter_by(
            ativo=True,
            tipo="carne"
        )
        .order_by(
            Produto.ordem.asc(),
            Produto.nome.asc()
        )
        .all()
    )

    acompanhamentos = (
        Produto.query
        .filter_by(
            ativo=True,
            tipo="acompanhamento"
        )
        .order_by(
            Produto.ordem.asc(),
            Produto.nome.asc()
        )
        .all()
    )

    adicionais = (
        Produto.query
        .filter_by(
            ativo=True,
            permite_adicional=True
        )
        .order_by(
            Produto.ordem.asc(),
            Produto.nome.asc()
        )
        .all()
    )

    bebidas = (
        Produto.query
        .filter_by(
            ativo=True,
            tipo="bebida"
        )
        .order_by(
            Produto.ordem.asc(),
            Produto.nome.asc()
        )
        .all()
    )

    sobremesas = (
        Produto.query
        .filter_by(
            ativo=True,
            tipo="sobremesa"
        )
        .order_by(
            Produto.ordem.asc(),
            Produto.nome.asc()
        )
        .all()
    )

    outros = (
        Produto.query
        .filter_by(
            ativo=True,
            tipo="outro"
        )
        .order_by(
            Produto.ordem.asc(),
            Produto.nome.asc()
        )
        .all()
    )

    # =====================================================
    # SALVAR MARMITEX
    # =====================================================

    if request.method == "POST":

        # =================================================
        # CARNE / PRATO
        # =================================================

        carne_id = request.form.get(
            "carne_id",
            type=int
        )

        carne = None

        if carne_id:

            carne = db.session.get(
                Produto,
                carne_id
            )

            if (
                not carne
                or not carne.ativo
                or carne.tipo != "carne"
            ):
                carne = None

        possui_outro_prato = False

        for produto in outros:

            quantidade = request.form.get(
                f"produto_{produto.id}",
                0,
                type=int
            )

            if (
                quantidade
                and quantidade > 0
            ):

                possui_outro_prato = True
                break

        if not carne and not possui_outro_prato:

            flash(
                "Selecione uma carne ou um prato para o Marmitex.",
                "danger"
            )

            return redirect(
                url_for(
                    "pedidos.novo_marmitex"
                )
            )

        # =================================================
        # NÚMERO DO MARMITEX
        # =================================================

        ultimo = (
            Pedido.query
            .filter(
                Pedido.tipo_atendimento == "marmitex",
                Pedido.numero_marmitex.isnot(None)
            )
            .order_by(
                Pedido.numero_marmitex.desc()
            )
            .first()
        )

        if ultimo:

            numero_marmitex = (
                ultimo.numero_marmitex + 1
            )

        else:

            numero_marmitex = 1

        # =================================================
        # CRIA PEDIDO
        # =================================================

        novo_pedido = Pedido(
            tipo_atendimento="marmitex",
            mesa_id=None,
            numero_marmitex=numero_marmitex,
            usuario_id=current_user.id,
            status="cozinha",
            subtotal=Decimal("0.00"),
            desconto=Decimal("0.00"),
            total=Decimal("0.00")
        )

        db.session.add(
            novo_pedido
        )

        db.session.flush()

        total_pedido = Decimal("0.00")

        item_prato = None

        # =================================================
        # CARNE PRINCIPAL
        # =================================================

        if carne:

            quantidade_prato = request.form.get(
                "quantidade_prato",
                1,
                type=int
            )

            if (
                quantidade_prato is None
                or quantidade_prato < 1
            ):
                quantidade_prato = 1

            valor_prato = (
                carne.preco
                * quantidade_prato
            )

            item_prato = ItemPedido(
                pedido_id=novo_pedido.id,
                produto_id=carne.id,
                tipo_item="normal",
                quantidade=quantidade_prato,
                valor_unitario=carne.preco,
                valor_total=valor_prato
            )

            db.session.add(
                item_prato
            )

            db.session.flush()

            total_pedido += valor_prato

        # =================================================
        # ACOMPANHAMENTOS
        # =================================================

        acompanhamento_ids = request.form.getlist(
            "acompanhamentos"
        )

        if item_prato:

            for acompanhamento_id in acompanhamento_ids:

                try:

                    acompanhamento_id = int(
                        acompanhamento_id
                    )

                except (TypeError, ValueError):

                    continue

                acompanhamento = db.session.get(
                    Produto,
                    acompanhamento_id
                )

                if (
                    acompanhamento
                    and acompanhamento.ativo
                    and acompanhamento.tipo == "acompanhamento"
                ):

                    vinculo = ItemPedidoAcompanhamento(
                        item_pedido_id=item_prato.id,
                        produto_id=acompanhamento.id
                    )

                    db.session.add(
                        vinculo
                    )

        # =================================================
        # ADICIONAIS
        # =================================================

        for adicional in adicionais:

            quantidade = request.form.get(
                f"adicional_{adicional.id}",
                0,
                type=int
            )

            if (
                quantidade is None
                or quantidade <= 0
            ):
                continue

            if adicional.preco_adicional is None:
                continue

            valor_total_adicional = (
                adicional.preco_adicional
                * quantidade
            )

            item_adicional = ItemPedido(
                pedido_id=novo_pedido.id,
                produto_id=adicional.id,
                tipo_item="adicional",
                quantidade=quantidade,
                valor_unitario=adicional.preco_adicional,
                valor_total=valor_total_adicional
            )

            db.session.add(
                item_adicional
            )

            total_pedido += (
                valor_total_adicional
            )

        # =================================================
        # BEBIDAS / SOBREMESAS / OUTROS
        # =================================================

        produtos_extras = (
            bebidas
            + sobremesas
            + outros
        )

        for produto in produtos_extras:

            quantidade = request.form.get(
                f"produto_{produto.id}",
                0,
                type=int
            )

            if (
                quantidade is None
                or quantidade <= 0
            ):
                continue

            if produto.preco is None:
                continue

            valor_total_item = (
                produto.preco
                * quantidade
            )

            item = ItemPedido(
                pedido_id=novo_pedido.id,
                produto_id=produto.id,
                tipo_item="normal",
                quantidade=quantidade,
                valor_unitario=produto.preco,
                valor_total=valor_total_item
            )

            db.session.add(
                item
            )

            total_pedido += (
                valor_total_item
            )

        # =================================================
        # TOTAL E DESTINO
        # =================================================

        novo_pedido.subtotal = total_pedido
        novo_pedido.total = total_pedido

        db.session.flush()

        possui_churrasqueira = any(
            getattr(
                item.produto,
                "destino_preparo",
                "sem_preparo"
            ) == "churrasqueira"
            for item in novo_pedido.itens
        )

        possui_cozinha = any(
            getattr(
                item.produto,
                "destino_preparo",
                "sem_preparo"
            ) == "cozinha"
            for item in novo_pedido.itens
        )

        if possui_churrasqueira:

            novo_pedido.status = "churrasqueira"

            novo_pedido.enviado_churrasqueira_em = (
                datetime.utcnow()
            )

        elif possui_cozinha:

            novo_pedido.status = "cozinha"

            novo_pedido.enviado_cozinha_em = (
                datetime.utcnow()
            )

        else:

            novo_pedido.status = "servido"
            novo_pedido.servido_em = datetime.utcnow()

        db.session.commit()

        # =================================================
        # IMPRESSÃO
        # =================================================

        try:

            imprimir_destinos_iniciais(
                novo_pedido
            )

        except Exception as erro:

            print(
                "ERRO IMPRESSÃO MARMITEX:",
                erro
            )

        if (
            possui_churrasqueira
            and possui_cozinha
        ):

            mensagem = (
                f"Marmitex #{numero_marmitex} enviado "
                "para churrasqueira e cozinha."
            )

        elif possui_churrasqueira:

            mensagem = (
                f"Marmitex #{numero_marmitex} enviado "
                "para a churrasqueira."
            )

        elif possui_cozinha:

            mensagem = (
                f"Marmitex #{numero_marmitex} enviado "
                "direto para a cozinha."
            )

        else:

            mensagem = (
                f"Marmitex #{numero_marmitex} registrado."
            )

        flash(
            mensagem,
            "success"
        )

        return redirect(
            url_for(
                "pedidos.detalhes",
                pedido_id=novo_pedido.id
            )
        )

    return render_template(
        "pedidos/marmitex.html",
        carnes=carnes,
        acompanhamentos=acompanhamentos,
        adicionais=adicionais,
        bebidas=bebidas,
        sobremesas=sobremesas,
        outros=outros
    )