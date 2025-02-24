$(document).ready(function () {
    console.log("🔹 Script de edição de referência carregado!");

    // 🔹 Adiciona um item na tabela de edição com a estrutura correta
    function adicionarItemNaTabela(tipo, id, descricao, preco) {
        let tabela = $(`#tabela-${tipo} tbody`);
        if (!tabela.length) {
            console.error(`Erro: Tabela '${tipo}' não encontrada.`);
            return;
        }

        // Verifica se o item já está na tabela para evitar duplicação
        if ($(`#tabela-${tipo} tbody tr[data-id="${id}"]`).length > 0) {
            console.warn(`O item ${id} já foi adicionado à tabela '${tipo}'.`);
            return;
        }

        let colunaProducao = tipo === "mao_obra"
            ? `<td><input type="number" name="${tipo}_producao[]" class="form-control producao-input" step="0.0001" min="0" value="1"></td>`
            : "";

        let colunaConsumo = `<td><input type="number" name="${tipo}_consumo[]" class="form-control consumo-input" step="0.0001" min="0" value="1"></td>`;
        let colunaPreco = (tipo === "componente" || tipo === "custo" || tipo === "mao_obra")
            ? `<td>R$ ${parseFloat(preco).toFixed(2)}</td>`
            : "";

        let novaLinha = `
            <tr data-id="${id}">
                <td><input type="hidden" name="${tipo}_id[]" value="${id}">${id}</td>
                <td>${descricao}</td>
                ${colunaPreco}
                ${colunaConsumo}
                ${colunaProducao}
                <td class="text-center" style="width: 120px;">
                    <button type="button" class="btn btn-danger btn-sm remover-item">Remover</button>
                </td>
            </tr>
        `;

        tabela.append(novaLinha);
    }
    // Remover itens da tabela sem excluir imediatamente do banco
    $(document).on("click", ".remover-item", function () {
        $(this).closest("tr").remove();
    });

    // 🔹 Selecionar itens nos modais
    $(document).on("click", ".selecionar-solado", function () {
        adicionarItemNaTabela("solado", $(this).data("id"), $(this).data("descricao"), $(this).data("preco"));
        $("#modalSolado").modal("hide");
    });

    $(document).on("click", ".selecionar-alca", function () {
        adicionarItemNaTabela("alca", $(this).data("id"), $(this).data("descricao"), $(this).data("preco"));
        $("#modalAlca").modal("hide");
    });

    $(document).on("click", ".selecionar-componente", function () {
        adicionarItemNaTabela("componente", $(this).data("id"), $(this).data("descricao"), $(this).data("preco"));
        $("#modalComponentes").modal("hide");
    });

    $(document).on("click", ".selecionar-custo", function () {
        adicionarItemNaTabela("custo", $(this).data("id"), $(this).data("descricao"), $(this).data("preco"));
        $("#modalCustos").modal("hide");
    });

    $(document).on("click", ".selecionar-mao", function () {
        adicionarItemNaTabela("mao_obra", $(this).data("id"), $(this).data("descricao"), $(this).data("diaria"));
        $("#modalMaoObra").modal("hide");
    });

    // 🔹 Antes de enviar o formulário, garantir que os campos vazios tenham valores padrão
    $("form").on("submit", function () {
        console.log("🔹 Preparando os valores antes de enviar...");

        $("input[type='number']").each(function () {
            if ($(this).val().trim() === "" || isNaN($(this).val())) {
                $(this).val(0);
            }
        });

        console.log("🔹 Formulário pronto para envio!");
    });
});
