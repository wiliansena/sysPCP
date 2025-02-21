document.addEventListener("DOMContentLoaded", function () {
    function adicionarItemNaTabela(tipo, id, descricao, preco) {
        let tabela = document.getElementById(`tabela-${tipo}`)?.querySelector("tbody");
        if (!tabela) {
            console.error(`Erro: Tabela '${tipo}' não encontrada.`);
            return;
        }

        let novaLinha = document.createElement("tr");
        novaLinha.setAttribute("data-id", id);

        let colunaProducao = "";
        if (tipo === "mao_obra") {
            colunaProducao = `<td><input type="number" name="${tipo}_producao[]" class="form-control producao-input" step="0.01" min="0"></td>`;
        }

        novaLinha.innerHTML = `
            <td><input type="hidden" name="${tipo}_id[]" value="${id}">${id}</td>
            <td>${descricao}</td>
            <td>R$ ${preco}</td>
            <td><input type="number" name="${tipo}_consumo[]" class="form-control consumo-input" step="0.01" min="0" value="0"></td>
            ${colunaProducao}
            <td class="preco-unitario">R$ 0.00</td>
            <td><button type="button" class="btn btn-danger btn-sm remover-item">Remover</button></td>
        `;

        tabela.appendChild(novaLinha);
        atualizarResumo();
    }

    // 🔹 Event listeners para os botões dos modais
    document.querySelectorAll(".selecionar-solado").forEach(button => {
        button.addEventListener("click", function () {
            adicionarItemNaTabela("solado", this.dataset.id, this.dataset.descricao, this.dataset.preco);
            $("#modalSolado").modal("hide");
        });
    });

    document.querySelectorAll(".selecionar-alca").forEach(button => {
        button.addEventListener("click", function () {
            adicionarItemNaTabela("alca", this.dataset.id, this.dataset.descricao, this.dataset.preco);
            $("#modalAlca").modal("hide");
        });
    });

    document.querySelectorAll(".selecionar-mao").forEach(button => {
        button.addEventListener("click", function () {
            adicionarItemNaTabela("mao_obra", this.dataset.id, this.dataset.descricao, this.dataset.diaria);
            $("#modalMaoObra").modal("hide");
        });
    });

    document.querySelectorAll(".selecionar-componente").forEach(button => {
        button.addEventListener("click", function () {
            adicionarItemNaTabela("componente", this.dataset.id, this.dataset.descricao, this.dataset.preco);
            $("#modalComponentes").modal("hide");
        });
    });

    document.querySelectorAll(".selecionar-custo").forEach(button => {
        button.addEventListener("click", function () {
            adicionarItemNaTabela("custo", this.dataset.id, this.dataset.descricao, this.dataset.preco);
            $("#modalCustos").modal("hide");
        });
    });

    // 🔹 Atualiza o preço unitário ao modificar o consumo
    document.addEventListener("input", function (event) {
        if (event.target.classList.contains("consumo-input") || event.target.classList.contains("producao-input")) {
            let row = event.target.closest("tr");
            let preco = parseFloat(row.cells[2].innerText.replace("R$ ", "").replace(",", ".")) || 0;
            let consumo = parseFloat(row.querySelector(".consumo-input").value) || 0;
            let producao = row.querySelector(".producao-input") ? parseFloat(row.querySelector(".producao-input").value) || 1 : 1;

            let precoUnitario = (preco * consumo) / producao;
            row.querySelector(".preco-unitario").innerText = `R$ ${precoUnitario.toFixed(2)}`;
            atualizarResumo();
        }
    });

    // 🔹 Função para atualizar o resumo de custos
    function atualizarResumo() {
        let totalSolado = 0, totalAlca = 0, totalComponente = 0, totalCusto = 0, totalMaoObra = 0;

        document.querySelectorAll("#tabela-solado tbody tr").forEach(row => {
            totalSolado += parseFloat(row.querySelector(".preco-unitario").innerText.replace("R$ ", "").replace(",", ".")) || 0;
        });

        document.querySelectorAll("#tabela-alca tbody tr").forEach(row => {
            totalAlca += parseFloat(row.querySelector(".preco-unitario").innerText.replace("R$ ", "").replace(",", ".")) || 0;
        });

        document.querySelectorAll("#tabela-componente tbody tr").forEach(row => {
            totalComponente += parseFloat(row.querySelector(".preco-unitario").innerText.replace("R$ ", "").replace(",", ".")) || 0;
        });

        document.querySelectorAll("#tabela-custo tbody tr").forEach(row => {
            totalCusto += parseFloat(row.querySelector(".preco-unitario").innerText.replace("R$ ", "").replace(",", ".")) || 0;
        });

        document.querySelectorAll("#tabela-mao_obra tbody tr").forEach(row => {
            totalMaoObra += parseFloat(row.querySelector(".preco-unitario").innerText.replace("R$ ", "").replace(",", ".")) || 0;
        });

        document.getElementById("total_solado").innerText = totalSolado.toFixed(2);
        document.getElementById("total_alcas").innerText = totalAlca.toFixed(2);
        document.getElementById("total_componentes").innerText = totalComponente.toFixed(2);
        document.getElementById("total_custos").innerText = totalCusto.toFixed(2);
        document.getElementById("total_mao_obra").innerText = totalMaoObra.toFixed(2);
    }

    // 🔹 Remover item ao clicar no botão de remover
    document.addEventListener("click", function (event) {
        if (event.target.classList.contains("remover-item")) {
            event.target.closest("tr").remove();
            atualizarResumo();
        }
    });
});
