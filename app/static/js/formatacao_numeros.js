$(document).ready(function () {
    // 🔹 Aplica apenas nos campos de peso
    $(document).on("input", "input[name*='peso_medio'], input[name*='peso_friso'], input[name*='peso_sem_friso']", function () {
        let valor = $(this).val();
        
        // Substitui a vírgula por ponto ao digitar
        valor = valor.replace(",", ".");
        
        // Garante que só tenha um único ponto decimal
        let partes = valor.split(".");
        if (partes.length > 2) {
            valor = partes[0] + "." + partes.slice(1).join("");
        }

        $(this).val(valor);
    });

    // 🔹 Aplica apenas no campo "Multiplicador"
    $(document).on("input", "input[name='multiplicador']", function () {
        let valor = $(this).val();

        // Substitui a vírgula por ponto
        valor = valor.replace(",", ".");

        // Permite apenas números e um único ponto decimal
        valor = valor.replace(/[^0-9.]/g, "");

        // Se houver mais de um ponto decimal, remove os extras
        let partes = valor.split(".");
        if (partes.length > 2) {
            valor = partes[0] + "." + partes.slice(1).join("");
        }

        $(this).val(valor);
    });
});

document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ JavaScript carregado! Aplicando formatação...");

    aplicarFormatacao(); // 🔹 Aplica a formatação no carregamento da página

    // 🔹 Aplica formatação nos campos de preço quando alterados manualmente
    document.querySelectorAll("input[name='preco'], input[name='encargos']").forEach(campo => {
        campo.addEventListener("input", function () {
            this.value = formatarNumeroParaInput(this.value);
        });
    });
});

// 🔹 Função para formatar números com separação de milhar e vírgula como decimal
function formatarNumeroParaExibicao(valor) {
    if (!valor) return "0,00";  // Se for vazio, retorna "0,00"

    let numero = parseFloat(valor).toFixed(2); // Garante duas casas decimais
    let partes = numero.split("."); // Divide o número entre parte inteira e decimal

    partes[0] = partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, "."); // Adiciona separação de milhar
    return partes.join(","); // Junta novamente com a vírgula no final corretamente
}


// 🔹 Função para converter valores digitados (substituir vírgula por ponto antes de salvar)
function formatarNumeroParaInput(valor) {
    if (!valor.trim()) return "";  // 🔹 Se o valor for vazio, permite limpar o campo

    valor = valor.replace(/\./g, ""); // 🔹 Remove pontos de milhar
    valor = valor.replace(",", "."); // 🔹 Troca a vírgula por ponto

    return valor;
}


// 🔹 Aplica a formatação correta nos elementos com `.preco-formatado`
function aplicarFormatacao() {
    document.querySelectorAll(".preco-formatado").forEach(el => {
        let valor = el.textContent.replace("R$ ", "").trim(); // 🔹 Remove "R$ " antes de formatar
        el.textContent = "R$ " + formatarNumeroParaExibicao(valor);
    });
}

