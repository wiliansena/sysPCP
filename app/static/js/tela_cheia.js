document.addEventListener("DOMContentLoaded", function () {
    // Restaurar automaticamente
    if (localStorage.getItem('modoTelaCheia') === '1') {
        document.querySelector('.top-bar').classList.add('d-none');
        document.querySelector('.sidebar').classList.add('d-none');
        document.querySelector('.content').classList.add('expandido');
        const btn = document.getElementById('btn-tela-cheia');
        if (btn) {
            btn.classList.add('active');
            btn.innerHTML = '<i class="fas fa-compress"></i> Sair Tela Cheia';
        }
    }

    // Botão de toggle
    const btn = document.getElementById('btn-tela-cheia');
    if (btn) {
        btn.addEventListener('click', function () {
            const topbar = document.querySelector('.top-bar');
            const sidebar = document.querySelector('.sidebar');
            const content = document.querySelector('.content');

            topbar.classList.toggle('d-none');
            sidebar.classList.toggle('d-none');
            content.classList.toggle('expandido');
            this.classList.toggle('active');

            // Salva o estado no localStorage
            localStorage.setItem('modoTelaCheia', this.classList.contains('active') ? '1' : '0');

            if (this.classList.contains('active')) {
                this.innerHTML = '<i class="fas fa-compress"></i> Sair Tela Cheia';
            } else {
                this.innerHTML = '<i class="fas fa-expand"></i> Tela Cheia';
            }
        });
    }
});
