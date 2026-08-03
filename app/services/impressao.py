from datetime import datetime


# =========================================================
# CONFIGURAÇÃO
# =========================================================

MODO_TESTE = True

IMPRESSORA_CHURRASQUEIRA = {
    "nome": "Churrasqueira",
    "ip": "192.168.0.201",
    "porta": 9100,
}

IMPRESSORA_COZINHA = {
    "nome": "Cozinha",
    "ip": "192.168.0.202",
    "porta": 9100,
}


# =========================================================
# AUXILIARES
# =========================================================

def linha():
    return "-" * 42


def titulo(texto):
    return texto.center(42)


def identificacao_pedido(pedido):

    linhas = []

    if pedido.tipo_atendimento == "marmitex":

        linhas.append(
            f"MARMITEX: #{pedido.numero_marmitex}"
        )

    else:

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


# =========================================================
# TICKET CHURRASQUEIRA
# =========================================================

def montar_ticket_churrasqueira(pedido):

    conteudo = []

    conteudo.append(
        titulo("BAR DO CABELUDO")
    )

    conteudo.append(linha())

    conteudo.append(
        titulo("CHURRASQUEIRA")
    )

    conteudo.append(linha())

    # =====================================================
    # IDENTIFICAÇÃO PRINCIPAL
    # =====================================================

    if pedido.tipo_atendimento == "marmitex":

        conteudo.append(
            titulo(
                f">>> MARMITEX #{pedido.numero_marmitex} <<<"
            )
        )

    else:

        conteudo.append(
            titulo(
                f">>> MESA {pedido.mesa.numero:02d} <<<"
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

    conteudo.append(linha())

    # =====================================================
    # CARNES
    # =====================================================

    encontrou_carne = False

    for item in pedido.itens:

        produto = item.produto

        if (
            produto.tipo == "carne"
            or item.tipo_item == "adicional"
        ):

            encontrou_carne = True

            if item.tipo_item == "adicional":

                conteudo.append(
                    f"{item.quantidade}x "
                    f"{produto.nome.upper()} "
                    f"[ADICIONAL]"
                )

            else:

                conteudo.append(
                    f"{item.quantidade}x "
                    f"{produto.nome.upper()}"
                )

    if not encontrou_carne:

        conteudo.append(
            "SEM CARNE"
        )

    conteudo.append(linha())

    # =====================================================
    # IDENTIFICAÇÃO NO FINAL
    # =====================================================

    if pedido.tipo_atendimento == "marmitex":

        conteudo.append(
            titulo(
                f"MARMITEX #{pedido.numero_marmitex}"
            )
        )

    else:

        conteudo.append(
            titulo(
                f"MESA {pedido.mesa.numero:02d}"
            )
        )

    conteudo.append("\n\n\n")

    return "\n".join(conteudo)


# =========================================================
# TICKET COZINHA
# =========================================================

def montar_ticket_cozinha(pedido):

    conteudo = []

    conteudo.append(
        titulo("BAR DO CABELUDO")
    )

    conteudo.append(linha())

    conteudo.append(
        titulo("COZINHA")
    )

    conteudo.append(linha())

    conteudo.extend(
        identificacao_pedido(pedido)
    )

    conteudo.append(linha())

    conteudo.append(
        "ACOMPANHAMENTOS"
    )

    conteudo.append("")

    encontrou = False

    for item in pedido.itens:

        for acompanhamento in item.acompanhamentos:

            encontrou = True

            conteudo.append(
                f"[X] {acompanhamento.produto.nome.upper()}"
            )

    if not encontrou:

        conteudo.append(
            "SEM ACOMPANHAMENTOS"
        )

    conteudo.append(linha())

    conteudo.append(
        f"CARNE LIBERADA: "
        f"{datetime.now().strftime('%H:%M')}"
    )

    conteudo.append("\n\n\n")

    return "\n".join(conteudo)


# =========================================================
# ENVIO
# =========================================================

def enviar_para_impressora(
    impressora,
    conteudo
):

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

    # Quando as Elgin chegarem,
    # entra aqui o envio ESC/POS pela rede.
    #
    # IP:
    # impressora["ip"]
    #
    # Porta:
    # impressora["porta"]

    return False


# =========================================================
# FUNÇÕES PÚBLICAS
# =========================================================

def imprimir_churrasqueira(pedido):

    conteudo = (
        montar_ticket_churrasqueira(
            pedido
        )
    )

    return enviar_para_impressora(
        IMPRESSORA_CHURRASQUEIRA,
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


# =========================================================
# TICKET - NOVO CONSUMO / CARNE ADICIONAL
# =========================================================

def montar_ticket_adicional_churrasqueira(
    pedido,
    itens_novos
):

    conteudo = []

    conteudo.append(
        titulo("BAR DO CABELUDO")
    )

    conteudo.append(linha())

    conteudo.append(
        titulo("*** NOVO CONSUMO ***")
    )

    conteudo.append(
        titulo("CHURRASQUEIRA")
    )

    conteudo.append(linha())

    conteudo.extend(
        identificacao_pedido(pedido)
    )

    conteudo.append(linha())

    for item in itens_novos:

        produto = item.produto

        texto = (
            f"{item.quantidade}x "
            f"{produto.nome.upper()}"
        )

        if item.tipo_item == "adicional":
            texto += " - ADICIONAL"

        conteudo.append(texto)

    conteudo.append(linha())

    if pedido.tipo_atendimento == "marmitex":

        conteudo.append(
            titulo(
                f"ADICIONAL - MARMITEX "
                f"#{pedido.numero_marmitex}"
            )
        )

    elif pedido.mesa:

        conteudo.append(
            titulo(
                f"ADICIONAL - MESA "
                f"{pedido.mesa.numero:02d}"
            )
        )

    conteudo.append("\n\n\n")

    return "\n".join(conteudo)


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