document.addEventListener("DOMContentLoaded", function () {
    function adicionarItemNaTabela(tipo, id, descricao, preco) {
        let tabela = document.getElementById(`tabela-${tipo}`)?.querySelector("tbody");
        if (!tabela) {
            console.error(`Erro: Tabela '${tipo}' não encontrada.`);
            return;
        }

        // Evitar adicionar itens duplicados
        if (document.querySelector(`#tabela-${tipo} tbody tr[data-id="${id}"]`)) {
            console.warn(`O item ${id} já foi adicionado à tabela '${tipo}'.`);
            return;
        }

        let novaLinha = document.createElement("tr");
        novaLinha.setAttribute("data-id", id);

        let colunaProducao = tipo === "mao_obra"
            ? `<td><input type="number" name="${tipo}_producao[]" class="form-control producao-input" step="0.0001" min="0" value="1"></td>`
            : "";

        let colunaConsumo = `
            <td><input type="number" name="${tipo}_consumo[]" class="form-control consumo-input" step="0.0001" min="0" value="1"></td>`;

        let colunaPrecoUnitario = `<td class="preco-unitario"><input type="hidden" name="${tipo}_preco_unitario[]" value="${preco}">R$ ${preco}</td>`;

        novaLinha.innerHTML = `
            <td><input type="hidden" name="${tipo}_id[]" value="${id}">${id}</td>
            <td>${descricao}</td>
            <td>R$ ${preco}</td>
            ${colunaConsumo}
            ${colunaProducao}
            ${colunaPrecoUnitario}
            <td><button type="button" class="btn btn-danger btn-sm remover-item">Remover</button></td>
        `;

        tabela.appendChild(novaLinha);
        atualizarResumo();
    }

    function atualizarResumo() {
        let totalSolado = 0, totalAlca = 0, totalComponente = 0, totalCusto = 0, totalMaoObra = 0;

        document.querySelectorAll("#tabela-solado tbody tr").forEach(row => {
            let precoUnitario = parseFloat(row.querySelector(".preco-unitario input").value) || 0;
            totalSolado += precoUnitario;
        });

        document.querySelectorAll("#tabela-alca tbody tr").forEach(row => {
            let precoUnitario = parseFloat(row.querySelector(".preco-unitario input").value) || 0;
            totalAlca += precoUnitario;
        });

        document.querySelectorAll("#tabela-componente tbody tr").forEach(row => {
            let precoUnitario = parseFloat(row.querySelector(".preco-unitario input").value) || 0;
            totalComponente += precoUnitario;
        });

        document.querySelectorAll("#tabela-custo tbody tr").forEach(row => {
            let precoUnitario = parseFloat(row.querySelector(".preco-unitario input").value) || 0;
            totalCusto += precoUnitario;
        });

        document.querySelectorAll("#tabela-mao_obra tbody tr").forEach(row => {
            let precoUnitario = parseFloat(row.querySelector(".preco-unitario input").value) || 0;
            totalMaoObra += precoUnitario;
        });

        document.getElementById("total_solado").innerText = totalSolado.toFixed(4);
        document.getElementById("total_alcas").innerText = totalAlca.toFixed(4);
        document.getElementById("total_componentes").innerText = totalComponente.toFixed(4);
        document.getElementById("total_operacional").innerText = totalCusto.toFixed(4);
        document.getElementById("total_mao_obra").innerText = totalMaoObra.toFixed(4);
    }

    document.addEventListener("input", function (event) {
        if (event.target.classList.contains("consumo-input") || event.target.classList.contains("producao-input")) {
            let row = event.target.closest("tr");
            let preco = parseFloat(row.cells[2].innerText.replace("R$ ", "").replace(",", ".")) || 0;
            let consumo = parseFloat(row.querySelector(".consumo-input").value) || 0;
            let producao = row.querySelector(".producao-input") ? parseFloat(row.querySelector(".producao-input").value) || 1 : 1;

            let tabela = row.closest("table");
            let tipo = tabela.id.replace("tabela-", "");

            let precoUnitario = (preco * consumo) / producao;
            row.querySelector(".preco-unitario").innerHTML = `<input type="hidden" name="${tipo}_preco_unitario[]" value="${precoUnitario.toFixed(4)}">R$ ${precoUnitario.toFixed(4)}`;
            atualizarResumo();
        }
    });

    document.addEventListener("click", function (event) {
        if (event.target.classList.contains("selecionar-solado")) {
            adicionarItemNaTabela("solado", event.target.dataset.id, event.target.dataset.descricao, event.target.dataset.preco);
            $("#modalSolado").modal("hide");
        }
        if (event.target.classList.contains("selecionar-alca")) {
            adicionarItemNaTabela("alca", event.target.dataset.id, event.target.dataset.descricao, event.target.dataset.preco);
            $("#modalAlca").modal("hide");
        }
        if (event.target.classList.contains("selecionar-mao")) {
            adicionarItemNaTabela("mao_obra", event.target.dataset.id, event.target.dataset.descricao, event.target.dataset.diaria);
            $("#modalMaoObra").modal("hide");
        }
        if (event.target.classList.contains("selecionar-componente")) {
            adicionarItemNaTabela("componente", event.target.dataset.id, event.target.dataset.descricao, event.target.dataset.preco);
            $("#modalComponentes").modal("hide");
        }
        if (event.target.classList.contains("selecionar-custo")) {
            adicionarItemNaTabela("custo", event.target.dataset.id, event.target.dataset.descricao, event.target.dataset.preco);
            $("#modalCustos").modal("hide");
        }
    });

    document.addEventListener("click", function (event) {
        if (event.target.classList.contains("remover-item")) {
            event.target.closest("tr").remove();
            atualizarResumo();
        }
    });

    document.querySelector("form").addEventListener("submit", function () {
        document.getElementById("input_total_solado").value = document.getElementById("total_solado").innerText;
        document.getElementById("input_total_alcas").value = document.getElementById("total_alcas").innerText;
        document.getElementById("input_total_componentes").value = document.getElementById("total_componentes").innerText;
        document.getElementById("input_total_operacional").value = document.getElementById("total_operacional").innerText;
        document.getElementById("input_total_mao_obra").value = document.getElementById("total_mao_obra").innerText;
    });
});
