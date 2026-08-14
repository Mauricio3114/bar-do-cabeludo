from datetime import datetime
import os
import platform

# =========================================================
# IMPRESSÃO WINDOWS
# =========================================================
# O Render roda Linux e não possui win32print.
# A impressão física será executada somente no ASUS/Windows.

if platform.system() == "Windows":
    try:
        import win32print
    except ImportError:
        win32print = None
else:
    win32print = None


# =========================================================
# CONFIGURAÇÃO
# =========================================================

MODO_TESTE = False


IMPRESSORA_CHURRASQUEIRA = {
    "nome": "Churrasqueira",
    "windows": "C3TECH IT-110",
}


IMPRESSORA_COZINHA = {
    "nome": "Cozinha",
    "windows": "C3TECH IT-110 COZINHA",
}


# =========================================================
# AUXILIARES
# =========================================================

def linha():
    return "-" * 42


def titulo(texto):
    return texto.center(42)


def destino_produto(produto):

    destino = getattr(
        produto,
        "destino_preparo",
        None
    )

    if destino in [
        "churrasqueira",
        "cozinha",
        "sem_preparo"
    ]:
        return destino

    return "sem_preparo"


def identificacao_pedido(pedido):

    linhas = []

    if pedido.tipo_atendimento == "marmitex":

        linhas.append(
            f"MARMITEX: #{pedido.numero_marmitex}"
        )

    elif pedido.mesa:

        linhas.append(
            f"MESA: {pedido.mesa.numero:02d}"
        )

    linhas.append(
        f"PEDIDO: #{pedido.id}"
    )

    linhas.append(
        f"GARCOM: {pedido.usuario.nome}"
    )

    linhas.append(
        f"HORA: {datetime.now().strftime('%H:%M')}"
    )

    return linhas


def identificacao_destaque(pedido):

    if pedido.tipo_atendimento == "marmitex":

        return titulo(
            f">>> MARMITEX #{pedido.numero_marmitex} <<<"
        )

    if pedido.mesa:

        return titulo(
            f">>> MESA {pedido.mesa.numero:02d} <<<"
        )

    return titulo(
        f">>> PEDIDO #{pedido.id} <<<"
    )


def identificacao_final(pedido):

    if pedido.tipo_atendimento == "marmitex":

        return titulo(
            f"MARMITEX #{pedido.numero_marmitex}"
        )

    if pedido.mesa:

        return titulo(
            f"MESA {pedido.mesa.numero:02d}"
        )

    return titulo(
        f"PEDIDO #{pedido.id}"
    )


def itens_por_destino(
    pedido,
    destino
):

    itens = []

    for item in pedido.itens:

        produto = item.produto

        if not produto:
            continue

        if destino_produto(produto) == destino:

            itens.append(item)

    return itens


# =========================================================
# TICKET CHURRASQUEIRA
# =========================================================

def montar_ticket_churrasqueira(
    pedido,
    itens=None
):

    if itens is None:

        itens = itens_por_destino(
            pedido,
            "churrasqueira"
        )

    if not itens:
        return None


    conteudo = []

    conteudo.append(
        titulo("BAR DO CABELUDO")
    )

    conteudo.append(
        linha()
    )

    conteudo.append(
        titulo("CHURRASQUEIRA")
    )

    conteudo.append(
        linha()
    )

    conteudo.append(
        identificacao_destaque(
            pedido
        )
    )

    conteudo.append("")

    conteudo.append(
        f"PEDIDO: #{pedido.id}"
    )

    conteudo.append(
        f"GARCOM: {pedido.usuario.nome.upper()}"
    )

    conteudo.append(
        f"HORA: {datetime.now().strftime('%H:%M')}"
    )

    conteudo.append(
        linha()
    )


    for item in itens:

        produto = item.produto

        if not produto:
            continue

        texto = (
            f"{item.quantidade}x "
            f"{produto.nome.upper()}"
        )

        if item.tipo_item == "adicional":

            texto += " [ADICIONAL]"

        conteudo.append(
            texto
        )

        # =================================================
        # CARNES ESCOLHIDAS DO PRATO MIXTO
        # =================================================

        carne_escolha_1 = getattr(
            item,
            "carne_escolha_1",
            None
        )

        carne_escolha_2 = getattr(
            item,
            "carne_escolha_2",
            None
        )

        if carne_escolha_1:

            conteudo.append(
                f"  > 1a CARNE: "
                f"{carne_escolha_1.nome.upper()}"
            )

        if carne_escolha_2:

            conteudo.append(
                f"  > 2a CARNE: "
                f"{carne_escolha_2.nome.upper()}"
                )


    conteudo.append(
        linha()
    )

    conteudo.append(
        identificacao_final(
            pedido
        )
    )

    conteudo.append(
        "\n\n\n"
    )

    return "\n".join(
        conteudo
    )


# =========================================================
# TICKET COZINHA - ITEM DIRETO
# =========================================================

def montar_ticket_cozinha_direta(
    pedido,
    itens=None
):

    if itens is None:

        itens = itens_por_destino(
            pedido,
            "cozinha"
        )

    if not itens:
        return None


    conteudo = []

    conteudo.append(
        titulo("BAR DO CABELUDO")
    )

    conteudo.append(
        linha()
    )

    conteudo.append(
        titulo("COZINHA")
    )

    conteudo.append(
        titulo("*** PEDIDO DIRETO ***")
    )

    conteudo.append(
        linha()
    )

    conteudo.append(
        identificacao_destaque(
            pedido
        )
    )

    conteudo.append("")

    conteudo.append(
        f"PEDIDO: #{pedido.id}"
    )

    conteudo.append(
        f"GARCOM: {pedido.usuario.nome.upper()}"
    )

    conteudo.append(
        f"HORA: {datetime.now().strftime('%H:%M')}"
    )

    conteudo.append(
        linha()
    )


    for item in itens:

        produto = item.produto

        texto = (
            f"{item.quantidade}x "
            f"{produto.nome.upper()}"
        )

        if item.tipo_item == "adicional":

            texto += " [ADICIONAL]"

        conteudo.append(
            texto
        )


    conteudo.append(
        linha()
    )

    conteudo.append(
        titulo(
            "PREPARO DIRETO NA COZINHA"
        )
    )

    conteudo.append(
        identificacao_final(
            pedido
        )
    )

    conteudo.append(
        "\n\n\n"
    )

    return "\n".join(
        conteudo
    )


# =========================================================
# TICKET COZINHA - ACOMPANHAMENTOS
# APÓS A CARNE SER LIBERADA
# =========================================================

def montar_ticket_cozinha(pedido):

    conteudo = []

    conteudo.append(
        titulo("BAR DO CABELUDO")
    )

    conteudo.append(
        linha()
    )

    conteudo.append(
        titulo("COZINHA")
    )

    conteudo.append(
        titulo("ACOMPANHAMENTOS")
    )

    conteudo.append(
        linha()
    )

    conteudo.append(
        identificacao_destaque(
            pedido
        )
    )

    conteudo.append("")

    conteudo.extend(
        identificacao_pedido(
            pedido
        )
    )

    conteudo.append(
        linha()
    )

    # =====================================================
    # SEPARA OS ACOMPANHAMENTOS POR PRATO
    # =====================================================

    encontrou = False
    numero_prato = 0

    for item in pedido.itens:

        # Adicionais/consumos avulsos não viram "PRATO"
        if item.tipo_item != "normal":
            continue

        # Só mostra pratos que possuem acompanhamentos
        if not item.acompanhamentos:
            continue

        numero_prato += 1
        encontrou = True

        produto = item.produto

        conteudo.append(
            f">>> PRATO {numero_prato} <<<"
        )

        if produto:

            conteudo.append(
                f"{item.quantidade}x "
                f"{produto.nome.upper()}"
            )

        conteudo.append(
            "-" * 24
        )

        for acompanhamento in item.acompanhamentos:

            conteudo.append(
                f"[X] "
                f"{acompanhamento.produto.nome.upper()}"
            )

        conteudo.append("")

    # =====================================================
    # CASO NÃO EXISTA ACOMPANHAMENTO
    # =====================================================

    if not encontrou:

        conteudo.append(
            "SEM ACOMPANHAMENTOS"
        )

    conteudo.append(
        linha()
    )

    conteudo.append(
        f"CARNE LIBERADA: "
        f"{datetime.now().strftime('%H:%M')}"
    )

    conteudo.append(
        identificacao_final(
            pedido
        )
    )

    conteudo.append(
        "\n\n\n"
    )

    return "\n".join(
        conteudo
    )


# =========================================================
# NOVO CONSUMO - CHURRASQUEIRA
# =========================================================

def montar_ticket_adicional_churrasqueira(
    pedido,
    itens_novos
):

    if not itens_novos:
        return None


    conteudo = []

    conteudo.append(
        titulo("BAR DO CABELUDO")
    )

    conteudo.append(
        linha()
    )

    conteudo.append(
        titulo("*** NOVO CONSUMO ***")
    )

    conteudo.append(
        titulo("CHURRASQUEIRA")
    )

    conteudo.append(
        linha()
    )

    conteudo.append(
        identificacao_destaque(
            pedido
        )
    )

    conteudo.append("")

    conteudo.extend(
        identificacao_pedido(
            pedido
        )
    )

    conteudo.append(
        linha()
    )


    for item in itens_novos:

        produto = item.produto

        if not produto:
            continue

        texto = (
            f"{item.quantidade}x "
            f"{produto.nome.upper()}"
        )

        if item.tipo_item == "adicional":

            texto += " [ADICIONAL]"

        conteudo.append(
            texto
        )

        # =================================================
        # CARNES ESCOLHIDAS DO PRATO MIXTO
        # =================================================

        carne_escolha_1 = getattr(
            item,
            "carne_escolha_1",
            None
        )

        carne_escolha_2 = getattr(
            item,
            "carne_escolha_2",
            None
        )

        if carne_escolha_1:

            conteudo.append(
                f"  > 1a CARNE: "
                f"{carne_escolha_1.nome.upper()}"
            )

        if carne_escolha_2:

            conteudo.append(
                f"  > 2a CARNE: "
                f"{carne_escolha_2.nome.upper()}"
            )

    conteudo.append(
        linha()
    )

    conteudo.append(
        titulo(
            "NOVO CONSUMO"
        )
    )

    conteudo.append(
        identificacao_final(
            pedido
        )
    )

    conteudo.append(
        "\n\n\n"
    )

    return "\n".join(
        conteudo
    )


# =========================================================
# NOVO CONSUMO - COZINHA
# =========================================================

def montar_ticket_adicional_cozinha(
    pedido,
    itens_novos
):

    if not itens_novos:
        return None

    conteudo = []

    conteudo.append(
        titulo("BAR DO CABELUDO")
    )

    conteudo.append(
        linha()
    )

    conteudo.append(
        titulo("*** NOVO PRATO ***")
    )

    conteudo.append(
        titulo("COZINHA")
    )

    conteudo.append(
        titulo("ACOMPANHAMENTOS")
    )

    conteudo.append(
        linha()
    )

    conteudo.append(
        identificacao_destaque(
            pedido
        )
    )

    conteudo.append("")

    conteudo.extend(
        identificacao_pedido(
            pedido
        )
    )

    conteudo.append(
        linha()
    )

    # =====================================================
    # MOSTRA CADA NOVO PRATO COM SEUS ACOMPANHAMENTOS
    # =====================================================

    encontrou = False
    numero_prato = 0

    for item in itens_novos:

        produto = item.produto

        if not produto:
            continue

        numero_prato += 1
        encontrou = True

        conteudo.append(
            f">>> NOVO PRATO {numero_prato} <<<"
        )

        conteudo.append(
            f"{item.quantidade}x "
            f"{produto.nome.upper()}"
        )

        conteudo.append(
            "-" * 24
        )

        if item.acompanhamentos:

            for acompanhamento in item.acompanhamentos:

                conteudo.append(
                    f"[X] "
                    f"{acompanhamento.produto.nome.upper()}"
                )

        else:

            conteudo.append(
                "SEM ACOMPANHAMENTOS"
            )

        if item.observacao:

            conteudo.append(
                f"OBS: {item.observacao.upper()}"
            )

        conteudo.append("")

    if not encontrou:

        conteudo.append(
            "SEM ITENS PARA PREPARAR"
        )

    conteudo.append(
        linha()
    )

    conteudo.append(
        titulo(
            "PREPARAR NA COZINHA"
        )
    )

    conteudo.append(
        identificacao_final(
            pedido
        )
    )

    conteudo.append(
        "\n\n\n"
    )

    return "\n".join(
        conteudo
    )


def enviar_para_impressora(
    impressora,
    conteudo
):

    if not conteudo:
        return True

    # =====================================================
    # AMBIENTE SEM IMPRESSÃO LOCAL
    # =====================================================
    # Render/Linux não possui win32print.
    # A impressão física acontece somente no ASUS/Windows.

    if win32print is None:

        print(
            f"[IMPRESSAO] Ambiente sem win32print. "
            f"Impressao local ignorada: {impressora['nome']}"
        )

        return True

    # =====================================================
    # MODO TESTE
    # =====================================================

    if MODO_TESTE:

        print("\n")
        print("=" * 60)

        print(
            f"IMPRESSAO TESTE -> "
            f"{impressora['nome'].upper()}"
        )

        print("=" * 60)
        print(conteudo)
        print("=" * 60)
        print("\n")

        return True

    # =====================================================
    # IMPRESSÃO REAL - WINDOWS / C3TECH IT-110
    # =====================================================

    try:

        nome_impressora = impressora["windows"]

        print(
            f"[IMPRESSAO] Enviando para "
            f"{nome_impressora}..."
        )

        # Abre a impressora instalada no Windows
        handle = win32print.OpenPrinter(
            nome_impressora
        )

        try:

            # Inicia um documento RAW no spooler
            win32print.StartDocPrinter(
                handle,
                1,
                (
                    "Bar do Cabeludo",
                    None,
                    "RAW"
                )
            )

            try:

                win32print.StartPagePrinter(
                    handle
                )

                # Inicializa a impressora ESC/POS
                dados = b"\x1b\x40"

                # Conteúdo do ticket
                dados += conteudo.encode(
                    "cp850",
                    errors="replace"
                )

                # Avança papel
                dados += b"\n\n\n"

                # Corte total ESC/POS
                dados += b"\x1d\x56\x00"

                win32print.WritePrinter(
                    handle,
                    dados
                )

                win32print.EndPagePrinter(
                    handle
                )

            finally:

                win32print.EndDocPrinter(
                    handle
                )

        finally:

            win32print.ClosePrinter(
                handle
            )

        print(
            f"[IMPRESSAO] OK -> "
            f"{impressora['nome']}"
        )

        return True

    except Exception as erro:

        print(
            f"[ERRO IMPRESSAO] "
            f"{impressora['nome']}: {erro}"
        )

        return False


# =========================================================
# FUNÇÕES PÚBLICAS
# =========================================================

def imprimir_churrasqueira(
    pedido,
    itens=None
):

    conteudo = (
        montar_ticket_churrasqueira(
            pedido,
            itens
        )
    )

    if not conteudo:
        return True

    return enviar_para_impressora(
        IMPRESSORA_CHURRASQUEIRA,
        conteudo
    )


def imprimir_cozinha_direta(
    pedido,
    itens=None
):

    conteudo = (
        montar_ticket_cozinha_direta(
            pedido,
            itens
        )
    )

    if not conteudo:
        return True

    return enviar_para_impressora(
        IMPRESSORA_COZINHA,
        conteudo
    )


def imprimir_cozinha(pedido):

    conteudo = (
        montar_ticket_cozinha(
            pedido
        )
    )

    return enviar_para_impressora(
        IMPRESSORA_COZINHA,
        conteudo
    )


def imprimir_adicional_churrasqueira(
    pedido,
    itens_novos
):

    if not itens_novos:
        return True


    conteudo = (
        montar_ticket_adicional_churrasqueira(
            pedido,
            itens_novos
        )
    )


    return enviar_para_impressora(
        IMPRESSORA_CHURRASQUEIRA,
        conteudo
    )


def imprimir_adicional_cozinha(
    pedido,
    itens_novos
):

    if not itens_novos:
        return True


    conteudo = (
        montar_ticket_adicional_cozinha(
            pedido,
            itens_novos
        )
    )


    return enviar_para_impressora(
        IMPRESSORA_COZINHA,
        conteudo
    )


# =========================================================
# IMPRESSÃO INICIAL POR DESTINO
# =========================================================

def imprimir_destinos_iniciais(pedido):

    itens_churrasqueira = (
        itens_por_destino(
            pedido,
            "churrasqueira"
        )
    )

    itens_cozinha = (
        itens_por_destino(
            pedido,
            "cozinha"
        )
    )


    if itens_churrasqueira:

        imprimir_churrasqueira(
            pedido,
            itens_churrasqueira
        )


    if itens_cozinha:

        imprimir_cozinha_direta(
            pedido,
            itens_cozinha
        )


    return {
        "churrasqueira": bool(
            itens_churrasqueira
        ),

        "cozinha": bool(
            itens_cozinha
        )
    }


# =========================================================
# NOVO CONSUMO POR DESTINO
# =========================================================

def imprimir_novo_consumo_por_destino(
    pedido,
    itens_novos
):

    itens_churrasqueira = []

    itens_cozinha = []


    for item in itens_novos:

        produto = item.produto

        destino = destino_produto(
            produto
        )


        if destino == "churrasqueira":

            itens_churrasqueira.append(
                item
            )


        elif destino == "cozinha":

            itens_cozinha.append(
                item
            )


    if itens_churrasqueira:

        imprimir_adicional_churrasqueira(
            pedido,
            itens_churrasqueira
        )


    if itens_cozinha:

        imprimir_adicional_cozinha(
            pedido,
            itens_cozinha
        )


    return True