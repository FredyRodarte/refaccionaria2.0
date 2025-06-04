function confirmarEliminacionUsuario(userId) {
    if (confirm('¿Estás seguro de que deseas eliminar este usuario?')) {
        window.location.href = '/eliminar_usuario/' + userId;
    }
}