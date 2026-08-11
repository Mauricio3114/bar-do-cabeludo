from app import db
from app.models.fila_impressao import FilaImpressao


# =========================================================
# CRIAR TRABALHO DE IMPRESSÃO
# =========================================================

def criar_trabalho_impressao(
    pedido,
    destino,
    tipo="pedido",
    itens=None
):

    if not pedido:
        return None

    if destino not in [
        "churrasqueira",
        "cozinha"
    ]:
        return None

    item_ids = None

    if itens:
        ids = []

        for item in itens:

            if getattr(item, "id", None):
                ids.append(
                    str(item.id)
                )

        if ids:
            item_ids = ",".join(ids)

    trabalho = FilaImpressao(
        pedido_id=pedido.id,
        destino=destino,
        tipo=tipo,
        item_ids=item_ids,
        status="pendente",
        tentativas=0
    )

    db.session.add(trabalho)

    return trabalho


# =========================================================
# FILA DO PEDIDO INICIAL
# =========================================================

def enfileirar_pedido_inicial(pedido):

    if not pedido:
        return

    possui_churrasqueira = any(
        getattr(
            item.produto,
            "destino_preparo",
            "sem_preparo"
        ) == "churrasqueira"
        for item in pedido.itens
    )

    possui_cozinha = any(
        getattr(
            item.produto,
            "destino_preparo",
            "sem_preparo"
        ) == "cozinha"
        for item in pedido.itens
    )

    if possui_churrasqueira:

        criar_trabalho_impressao(
            pedido=pedido,
            destino="churrasqueira",
            tipo="pedido"
        )

    if possui_cozinha:

        criar_trabalho_impressao(
            pedido=pedido,
            destino="cozinha",
            tipo="pedido"
        )


# =========================================================
# FILA DA COZINHA
# CARNE LIBERADA PELA CHURRASQUEIRA
# =========================================================

def enfileirar_cozinha(pedido):

    if not pedido:
        return

    criar_trabalho_impressao(
        pedido=pedido,
        destino="cozinha",
        tipo="pedido"
    )


# =========================================================
# FILA DE NOVO CONSUMO
# =========================================================

def enfileirar_novo_consumo(
    pedido,
    itens
):

    if not pedido or not itens:
        return

    itens_churrasqueira = []
    itens_cozinha = []

    for item in itens:

        produto = getattr(
            item,
            "produto",
            None
        )

        if not produto:
            continue

        destino = getattr(
            produto,
            "destino_preparo",
            "sem_preparo"
        )

        if destino == "churrasqueira":
            itens_churrasqueira.append(item)

        elif destino == "cozinha":
            itens_cozinha.append(item)

    if itens_churrasqueira:

        criar_trabalho_impressao(
            pedido=pedido,
            destino="churrasqueira",
            tipo="novo_consumo",
            itens=itens_churrasqueira
        )

    if itens_cozinha:

        criar_trabalho_impressao(
            pedido=pedido,
            destino="cozinha",
            tipo="novo_consumo",
            itens=itens_cozinha
        )